from __future__ import annotations

import builtins

import pytest

from apps.agent.providers import ProviderError, RealProcessProvider, RealScreenCaptureProvider, RealWebcamProvider, build_providers


def test_fake_providers_do_not_require_optional_deps() -> None:
    providers = build_providers("fake")
    assert providers.processes.list_processes()
    assert providers.webcam.set_webcam(False, consent=False)["webcam"] == "stopped"


def test_real_screen_reports_missing_optional_dependency(monkeypatch) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "mss":
            raise ImportError("missing mss")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ProviderError, match="mss is not installed"):
        RealScreenCaptureProvider().capture_jpeg_b64()


def test_real_process_reports_missing_optional_dependency(monkeypatch) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError("missing psutil")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ProviderError, match="psutil is not installed"):
        RealProcessProvider().list_processes()


def test_real_webcam_reports_missing_optional_dependency(monkeypatch) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "cv2":
            raise ImportError("missing cv2")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ProviderError, match="opencv-python is not installed"):
        RealWebcamProvider().set_webcam(True, consent=True)

