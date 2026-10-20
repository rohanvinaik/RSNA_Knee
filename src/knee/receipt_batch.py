"""Coordinator-owned receipt metadata staging for a single no-draw run."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

_PENDING_SCHEMA = "receipt-pending-v1"
_PENDING_FIELDS = {
    "schema",
    "study_uid",
    "series_uids",
    "request",
    "records",
    "unread",
    "telemetry",
    "objects",
}


class ReceiptBatch:
    """Stage complete study updates, then publish one merged receipt atomically."""

    def __init__(
        self,
        run_dir: Path,
        request: Mapping[str, Any],
        *,
        load_json: Callable[[Path], Any],
        compressed_path: Callable[[Path], Path],
        dump_json_atomic: Callable[..., Any],
        merged_receipt: Callable[..., dict],
        default: Callable[[Any], Any] | None = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.receipt_path = self.run_dir / "receipt.json"
        self.pending_dir = self.run_dir / ".receipt-pending"
        self.request = dict(request)
        self.load_json = load_json
        self.compressed_path = compressed_path
        self.dump_json_atomic = dump_json_atomic
        self.merged_receipt = merged_receipt
        self.default = default
        self.run_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.current = self.load_json(self.receipt_path)
        except FileNotFoundError:
            self.current = None
        self.pending_paths: list[Path] = []
        self.dirty = False
        self.next_sequence = 0
        self._recover_pending()

    def _recover_pending(self) -> None:
        if not self.pending_dir.exists():
            return
        entries = sorted(self.pending_dir.iterdir(), key=lambda path: path.name)
        for path in entries:
            if not path.is_file() or not path.name.endswith(".json.xz"):
                raise ValueError("receipt_pending_unrecognized_entry")
            payload = self.load_json(path)
            self._validate_pending(payload)
            self.current = self._merge_payload(self.current, payload)
            self.pending_paths.append(path)
            sequence_text = path.name.removesuffix(".json.xz")
            if (
                len(sequence_text) != 20
                or not sequence_text.isascii()
                or not sequence_text.isdigit()
            ):
                raise ValueError("receipt_pending_incompatible")
            sequence = int(sequence_text)
            self.next_sequence = max(self.next_sequence, sequence + 1)
        if entries:
            self.dirty = True

    @staticmethod
    def _validate_pending(payload: Any) -> None:
        if not isinstance(payload, dict) or set(payload) != _PENDING_FIELDS:
            raise ValueError("receipt_pending_incompatible")
        if payload["schema"] != _PENDING_SCHEMA:
            raise ValueError("receipt_pending_incompatible")
        if not isinstance(payload["study_uid"], str) or not payload["study_uid"]:
            raise ValueError("receipt_pending_incompatible")
        if not isinstance(payload["series_uids"], list):
            raise ValueError("receipt_pending_incompatible")  # noqa: TRY004
        if not isinstance(payload["request"], dict):
            raise ValueError("receipt_pending_incompatible")  # noqa: TRY004
        if not isinstance(payload["records"], list):
            raise ValueError("receipt_pending_incompatible")  # noqa: TRY004
        if not isinstance(payload["unread"], dict):
            raise ValueError("receipt_pending_incompatible")  # noqa: TRY004
        if payload["telemetry"] is not None and not isinstance(
            payload["telemetry"], dict
        ):
            raise ValueError("receipt_pending_incompatible")
        if payload["objects"] is not None and not isinstance(payload["objects"], dict):
            raise ValueError("receipt_pending_incompatible")

    def _merge_payload(self, receipt: Any, payload: Mapping[str, Any]) -> dict:
        return self.merged_receipt(
            receipt,
            payload["request"],
            payload["study_uid"],
            payload["series_uids"],
            payload["records"],
            payload["unread"],
            payload["telemetry"],
            payload["objects"],
        )

    def add(
        self,
        study_uid: str,
        series_uids: Sequence[str],
        records: Sequence[dict],
        unread: Mapping[str, Any],
        telemetry: Mapping[str, Any] | None,
        objects: Mapping[str, Any] | None = None,
    ) -> None:
        payload = {
            "schema": _PENDING_SCHEMA,
            "study_uid": study_uid,
            "series_uids": list(series_uids),
            "request": self.request,
            "records": list(records),
            "unread": dict(unread),
            "telemetry": None if telemetry is None else dict(telemetry),
            "objects": None if objects is None else dict(objects),
        }
        self._validate_pending(payload)
        merged = self._merge_payload(self.current, payload)
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        stem = self.pending_dir / f"{self.next_sequence:020d}.json"
        path = self.compressed_path(stem)
        self.dump_json_atomic(path, payload, default=self.default)
        self.pending_paths.append(path)
        self.next_sequence += 1
        self.current = merged
        self.dirty = True

    def finalize(self) -> None:
        if not self.dirty:
            if self.pending_dir.exists():
                self.pending_dir.rmdir()
            return
        self.dump_json_atomic(self.receipt_path, self.current, default=self.default)
        for path in self.pending_paths:
            path.unlink()
        if self.pending_dir.exists():
            self.pending_dir.rmdir()
        self.pending_paths.clear()
        self.dirty = False

    def finalize_after_failure(self, original: BaseException) -> None:
        """Finalize durable staged data without replacing the original failure."""
        try:
            self.finalize()
        except Exception as error:  # noqa: BLE001
            note = f"receipt finalization also failed: {error!r}"
            if hasattr(original, "add_note"):
                original.add_note(note)


class ReceiptBatches:
    """The two receipt files owned by the run coordinator."""

    def __init__(
        self,
        run_dir: Path,
        main_run: Path,
        request: Mapping[str, Any],
        *,
        load_json: Callable[[Path], Any],
        compressed_path: Callable[[Path], Path],
        dump_json_atomic: Callable[..., Any],
        merged_receipt: Callable[..., dict],
        default: Callable[[Any], Any] | None = None,
    ) -> None:
        kwargs = {
            "load_json": load_json,
            "compressed_path": compressed_path,
            "dump_json_atomic": dump_json_atomic,
            "merged_receipt": merged_receipt,
            "default": default,
        }
        self.interiors = ReceiptBatch(run_dir, request, **kwargs)
        self.main = ReceiptBatch(main_run, request, **kwargs)

    def add_study(self, result: Mapping[str, Any]) -> None:
        uid = result["study_uid"]
        self.interiors.add(
            uid,
            result["series_uids"],
            result["records"],
            result["unread"],
            result["telemetry"],
            result["objects"],
        )
        self.main.add(
            uid,
            result["main_keys"],
            result["main_records"],
            result["main_unread"],
            None,
            None,
        )

    def finalize(self) -> None:
        self.interiors.finalize()
        self.main.finalize()

    def finalize_after_failure(self, original: BaseException) -> None:
        failures = []
        for batch in (self.interiors, self.main):
            try:
                batch.finalize()
            except Exception as error:  # noqa: BLE001
                # Preserve the original measurement failure and annotate cleanup errors.
                failures.append(error)
        for error in failures:
            note = f"receipt finalization also failed: {error!r}"
            if hasattr(original, "add_note"):
                original.add_note(note)
