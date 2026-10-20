from __future__ import annotations

from knee.encoding import carrier as carrier_module
from knee.encoding.carrier import HadamardCarrier


def test_immutable_carrier_identity_is_fingerprinted_once_per_instance(monkeypatch):
    calls = []
    original = carrier_module._fingerprint

    def counted(permutation):
        calls.append(permutation)
        return original(permutation)

    monkeypatch.setattr(carrier_module, "_fingerprint", counted)
    carrier = HadamardCarrier.from_banks(("native", "geometry"))

    first = carrier.identity
    assert len(calls) == 2
    assert carrier.identity == first
    assert len(calls) == 2

    equivalent = HadamardCarrier.from_banks(("native", "geometry"))
    assert equivalent.identity == first
    assert len(calls) == 4
