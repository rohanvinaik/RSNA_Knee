"""Build kaggle/decoder_probe/: a private, offline Kaggle kernel that measures pixel decoding there (operational).

The competition names four transfer syntaxes; every local file so far is uncompressed, and a normal kernel run
mounts only the three public test studies. So the probe carries its own compressed files: a synthetic image (the
same deterministic pattern as tests/knee/study/conftest.py, no competition data) written uncompressed and
re-encoded here by GDCM into each syntax, embedded as base64. On Kaggle it reports the interpreter, pydicom, the
decoder plugins present, an exact decode of each embedded file, and a decode of every mounted test file.

Usage (from the repo root): .venv/bin/python tools/build_decoder_probe.py
Then push and read it: kaggle kernels push -p kaggle/decoder_probe
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import gdcm
import numpy as np
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import (
    UID,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    MRImageStorage,
    generate_uid,
)

OUT = Path("kaggle/decoder_probe")
ROWS, COLUMNS = 16, 24
GDCM_SYNTAXES = {
    "1.2.840.10008.1.2.4.57": "JPEGLosslessProcess14",
    "1.2.840.10008.1.2.4.70": "JPEGLosslessProcess14_1",
    "1.2.840.10008.1.2.4.90": "JPEG2000Lossless",
    "1.2.840.10008.1.2.4.91": "JPEG2000",
}
METADATA = {
    "id": "rohanvinaik/rsna-knee-decoder-probe",
    "title": "rsna knee decoder probe",
    "code_file": "probe.py",
    "language": "python",
    "kernel_type": "script",
    "is_private": True,
    "enable_gpu": False,
    "enable_internet": False,
    "competition_sources": ["rsna-knee-abnormality-detection"],
}

PROBE = '''"""Measure pixel decoding in this kernel: built by tools/build_decoder_probe.py, which embeds the fixtures."""

import base64
import importlib
import io
import json
import platform
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pydicom
from pydicom.pixels.decoders.base import get_decoder
from pydicom.uid import UID

FIXTURES = __FIXTURES__
LOSSLESS = {"1.2.840.10008.1.2", "1.2.840.10008.1.2.4.57", "1.2.840.10008.1.2.4.70", "1.2.840.10008.1.2.4.90"}
EXPECTED = (np.arange(__ROWS__ * __COLUMNS__, dtype=np.int64) * 37 % 4093).reshape(__ROWS__, __COLUMNS__).astype(np.uint16)


def module_version(name):
    try:
        module = importlib.import_module(name)
    # BLE001: any failure to import is the measurement, reported by its type
    except Exception as exc:  # noqa: BLE001
        return f"absent ({type(exc).__name__})"
    return str(getattr(module, "__version__", "imported"))


def decode(blob, uid):
    try:
        pixels = pydicom.dcmread(io.BytesIO(base64.b64decode(blob))).pixel_array
    # BLE001: any failure to decode is the measurement, reported with its message
    except Exception as exc:  # noqa: BLE001
        return {"decoded": False, "error": f"{type(exc).__name__}: {exc}"[:300]}
    exact = bool(np.array_equal(pixels, EXPECTED)) if uid in LOSSLESS else None
    return {"decoded": True, "shape": list(pixels.shape), "dtype": str(pixels.dtype), "exact": exact}


def mounted():
    roots = [p.parent for p in Path("/kaggle/input").glob("**/test_series") if p.is_dir()]
    if not roots:
        return {"root": None}
    root = roots[0]
    syntaxes, failed, files = Counter(), Counter(), 0
    for path in sorted((root / "test_series").rglob("*.dcm")):
        files += 1
        ds = pydicom.dcmread(path)
        uid = str(ds.file_meta.TransferSyntaxUID)
        syntaxes[UID(uid).name] += 1
        try:
            _ = ds.pixel_array
        # BLE001: any failure to decode a mounted file is counted, by its syntax
        except Exception:  # noqa: BLE001
            failed[UID(uid).name] += 1
    return {"root": str(root), "files": files, "syntaxes": dict(syntaxes), "failed": dict(failed)}


report = {
    "python": sys.version,
    "platform": platform.platform(),
    "pydicom": pydicom.__version__,
    "numpy": np.__version__,
    "modules": {name: module_version(name) for name in ("gdcm", "pylibjpeg", "libjpeg", "openjpeg", "PIL")},
    "decoders": {
        UID(uid).name: {
            "available": get_decoder(UID(uid)).is_available,
            "plugins": sorted(get_decoder(UID(uid)).available_plugins),
        }
        for uid in FIXTURES
    },
    "fixtures": {UID(uid).name: decode(blob, uid) for uid, blob in FIXTURES.items()},
    "mounted": mounted(),
}
text = json.dumps(report, indent=2)
print(text)
Path("/kaggle/working/probe.json").write_text(text)
'''


def pattern() -> np.ndarray:
    values = np.arange(ROWS * COLUMNS, dtype=np.int64) * 37 % 4093
    return values.reshape(ROWS, COLUMNS).astype(np.uint16)


def write_plain(path: Path, syntax: UID) -> Path:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = MRImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = syntax
    ds = Dataset()
    ds.file_meta = meta
    ds.SOPClassUID = MRImageStorage
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.Modality = "MR"
    ds.Rows, ds.Columns = ROWS, COLUMNS
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.PixelData = pattern().tobytes()
    ds.save_as(path, enforce_file_format=True)
    return path


def transcode(source: Path, target: Path, syntax: str) -> Path:
    reader = gdcm.ImageReader()
    reader.SetFileName(str(source))
    if not reader.Read():
        raise RuntimeError(f"gdcm could not read {source}")
    change = gdcm.ImageChangeTransferSyntax()
    change.SetTransferSyntax(gdcm.TransferSyntax(getattr(gdcm.TransferSyntax, syntax)))
    change.SetInput(reader.GetImage())
    if not change.Change():
        raise RuntimeError(f"gdcm could not encode as {syntax}")
    writer = gdcm.ImageWriter()
    writer.SetFileName(str(target))
    writer.SetFile(reader.GetFile())
    writer.SetImage(change.GetOutput())
    if not writer.Write():
        raise RuntimeError(f"gdcm could not write {target}")
    return target


def fixtures() -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        plain = write_plain(work / "plain.dcm", ExplicitVRLittleEndian)
        files = {
            str(ImplicitVRLittleEndian): write_plain(
                work / "implicit.dcm", ImplicitVRLittleEndian
            )
        }
        for uid, name in GDCM_SYNTAXES.items():
            files[uid] = transcode(plain, work / f"{name}.dcm", name)
        return {
            uid: base64.b64encode(path.read_bytes()).decode("ascii")
            for uid, path in files.items()
        }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    probe = (
        PROBE.replace("__FIXTURES__", json.dumps(fixtures(), indent=4))
        .replace("__ROWS__", str(ROWS))
        .replace("__COLUMNS__", str(COLUMNS))
    )
    (OUT / "probe.py").write_text(probe, encoding="utf-8")
    (OUT / "kernel-metadata.json").write_text(
        json.dumps(METADATA, indent=2) + "\n", encoding="utf-8"
    )
    ruff = Path(sys.executable).with_name("ruff")
    subprocess.run([str(ruff), "format", str(OUT / "probe.py")], check=True)
    print(f"wrote {OUT / 'probe.py'} (formatted) and {OUT / 'kernel-metadata.json'}")


if __name__ == "__main__":
    main()
