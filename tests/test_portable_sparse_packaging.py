from __future__ import annotations

import hashlib
import importlib.util
import sys
import tarfile
from pathlib import Path

import pytest

from knee.diagnosis.product_cases import profiles_from_product
from knee.diagnosis.squint_memory import (
    full_profile_from_case,
    hydrate_full_profiles,
    load_memory,
    save_memory,
)

REPO = Path(__file__).resolve().parents[1]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("wrapper_name", ["production", "scaling"])
@pytest.mark.parametrize("shape", ["tar", "auto_extracted"])
def test_portable_sparse_full_profiles_package_offline(
    tmp_path: Path, wrapper_name: str, shape: str
) -> None:
    fixture_module = _load_module(
        REPO / "tests/test_squint_full_profiles.py", "squint_full_profile_fixture"
    )
    product = tmp_path / "products" / "study-portable-full.h5"
    product.parent.mkdir()
    manifest, record = fixture_module._fixture_product(product)
    legacy = fixture_module._legacy_memory(product, manifest, record)
    expected_full = profiles_from_product(product, mode="full")[0]
    hydrated = hydrate_full_profiles(legacy, product.parent)
    memory_dir = tmp_path / "memory"
    save_memory(hydrated, memory_dir)
    product.unlink()
    assert not product.exists()

    packager = _load_module(
        REPO / "scripts/package_squint_kaggle.py", "portable_memory_packager"
    )
    wrapper_file = (
        REPO / "kaggle/squint-production/run_squint.py"
        if wrapper_name == "production"
        else REPO / "kaggle/squint-scaling/run_scaling.py"
    )
    wrapper = _load_module(wrapper_file, f"portable_memory_{wrapper_name}_wrapper")
    staging = tmp_path / "staging"
    packager.build_staging(memory_dir, staging, REPO)
    verified = packager.verify_staging(staging, memory=memory_dir, root=REPO)
    assert verified["memory"]["entry"] == "memory"

    if shape == "tar":
        manifest_path = staging / packager.MANIFEST_NAME
        runtime_manifest = wrapper.load_manifest(manifest_path)
        copied = wrapper.materialise(
            manifest_path, runtime_manifest, tmp_path / "local-bundle"
        )
        assert copied["mode"] == "tar"
        local_bundle = tmp_path / "local-bundle"
    else:
        nested = tmp_path / "input" / "runtime-bundle"
        nested.mkdir(parents=True)
        with tarfile.open(staging / packager.TAR_NAME, "r:") as archive:
            for member in archive:
                source = archive.extractfile(member)
                assert source is not None
                target = nested / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read())
        manifest_path = nested / packager.MANIFEST_NAME
        runtime_manifest = wrapper.load_manifest(manifest_path)
        copied = wrapper.materialise(
            manifest_path, runtime_manifest, tmp_path / "local-bundle"
        )
        assert copied["mode"] == "directory"
        local_bundle = tmp_path / "local-bundle"

    bundled_memory = local_bundle / "memory"
    loaded = load_memory(bundled_memory)
    case = next(item for item in loaded["cases"] if item["subject"] == "femur")
    actual_full = full_profile_from_case(loaded, case)
    assert actual_full.bundle == expected_full.bundle
    assert actual_full.source_id == expected_full.source_id
    assert case["condition_calls"] == {"ACL": 1}
    assert case["profile"]["banks"] == legacy["cases"][0]["profile"]["banks"]
    assert loaded["full_profile_contexts"] == hydrated["full_profile_contexts"]
    assert loaded["full_profile_payloads"] == hydrated["full_profile_payloads"]
    assert (
        hashlib.sha256((staging / packager.TAR_NAME).read_bytes()).hexdigest()
        == verified["tar_sha256"]
    )
