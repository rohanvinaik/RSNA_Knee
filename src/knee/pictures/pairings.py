"""Pass the selected-plane pairing record unchanged to drawing."""

from knee.relations.pairings import PairingReading


def panels(reading: PairingReading) -> PairingReading:
    """No measurement, count, reconstruction or decision occurs in this adapter."""
    return reading
