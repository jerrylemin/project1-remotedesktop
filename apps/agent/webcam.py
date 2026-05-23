from __future__ import annotations


def webcam_status(start: bool, consent: bool) -> dict[str, object]:
    if start and not consent:
        raise PermissionError("webcam requires explicit consent")
    return {"webcam": "started" if start else "stopped", "consent": consent}

