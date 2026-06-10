from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from apps.agent.app_manager import list_applications, start_application, stop_application
from apps.agent.input_demo import handle_input_event
from apps.agent.job_runner import command_from_schema, run_job
from apps.agent.process_manager import list_processes, stop_process
from apps.agent.sandbox import job_sandbox
from apps.agent.screen import fake_jpeg_frame, frame_payload, real_jpeg_frame
from apps.agent.webcam import encode_cv2_frame, fake_webcam_frame, webcam_fps, webcam_height, webcam_status, webcam_width


class ProviderError(RuntimeError):
    pass


class ScreenCaptureProvider(ABC):
    @abstractmethod
    def capture_jpeg_b64(self) -> str:
        raise NotImplementedError

    def capture_frame(self, machine_id: str, session_id: str | None = None, frame_no: int = 1) -> dict[str, Any]:
        return frame_payload(self.capture_jpeg_b64(), machine_id=machine_id, session_id=session_id, frame_no=frame_no)


class ProcessProvider(ABC):
    @abstractmethod
    def list_processes(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def stop_process(self, pid: int, confirm: bool) -> dict[str, Any]:
        raise NotImplementedError


class AppLauncher(ABC):
    @abstractmethod
    def list_applications(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def start_application(self, command: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def stop_application(self, name: str, confirm: bool) -> dict[str, Any]:
        raise NotImplementedError


class WebcamProvider(ABC):
    @abstractmethod
    def set_webcam(self, start: bool, consent: bool, device_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def snapshot(self, machine_id: str) -> dict[str, Any]:
        raise NotImplementedError


class InputController(ABC):
    @abstractmethod
    def handle_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class SandboxRunner(ABC):
    @abstractmethod
    async def run(self, machine_id: str, sandbox_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class FakeScreenCaptureProvider(ScreenCaptureProvider):
    def capture_jpeg_b64(self) -> str:
        return fake_jpeg_frame()


class RealScreenCaptureProvider(ScreenCaptureProvider):
    def capture_jpeg_b64(self) -> str:
        try:
            import mss  # noqa: F401
        except ImportError as exc:
            raise ProviderError("mss is not installed; install real-agent optional dependencies") from exc
        return real_jpeg_frame()


class FakeProcessProvider(ProcessProvider):
    def list_processes(self) -> list[dict[str, Any]]:
        return [{"pid": 101, "name": "fake-editor", "status": "running"}, {"pid": 102, "name": "fake-browser", "status": "sleeping"}]

    def stop_process(self, pid: int, confirm: bool) -> dict[str, Any]:
        if not confirm:
            raise ProviderError("process stop requires confirmation")
        return {"pid": pid, "stopped": True, "fake": True}


class RealProcessProvider(ProcessProvider):
    def list_processes(self) -> list[dict[str, Any]]:
        try:
            import psutil  # noqa: F401
        except ImportError as exc:
            raise ProviderError("psutil is not installed; process list unavailable") from exc
        return list_processes()

    def stop_process(self, pid: int, confirm: bool) -> dict[str, Any]:
        return stop_process(pid, confirm)


class FakeAppLauncher(AppLauncher):
    def list_applications(self) -> list[dict[str, Any]]:
        return [{"name": "fake-notepad", "allowed": True}, {"name": "fake-calculator", "allowed": True}]

    def start_application(self, command: str) -> dict[str, Any]:
        return {"pid": 999, "command": command, "fake": True}

    def stop_application(self, name: str, confirm: bool) -> dict[str, Any]:
        if not confirm:
            raise ProviderError("application stop requires confirmation")
        return {"name": name, "stopped": True, "fake": True}


class RealAppLauncher(AppLauncher):
    def list_applications(self) -> list[dict[str, Any]]:
        return list_applications()

    def start_application(self, command: str) -> dict[str, Any]:
        return start_application(command)

    def stop_application(self, name: str, confirm: bool) -> dict[str, Any]:
        return stop_application(name, confirm)


class FakeWebcamProvider(WebcamProvider):
    def set_webcam(self, start: bool, consent: bool, device_id: str | None = None) -> dict[str, Any]:
        if start and not consent:
            raise ProviderError("webcam requires explicit consent")
        return {"webcam": "started" if start else "stopped", "fake": True, "device_id": device_id}

    def snapshot(self, machine_id: str) -> dict[str, Any]:
        return fake_webcam_frame(machine_id)


class RealWebcamProvider(WebcamProvider):
    def __init__(self) -> None:
        self._capture = None
        self._frame_no = 0

    def set_webcam(self, start: bool, consent: bool, device_id: str | None = None) -> dict[str, Any]:
        try:
            import cv2
        except ImportError as exc:
            raise ProviderError("opencv-python is not installed; webcam unavailable") from exc
        if start and consent:
            self._release()
            index = int((device_id or "camera-0").removeprefix("camera-"))
            capture = cv2.VideoCapture(index)
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, webcam_width())
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, webcam_height())
            capture.set(cv2.CAP_PROP_FPS, webcam_fps())
            try:
                capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            except Exception:
                pass
            if not capture.isOpened():
                capture.release()
                raise ProviderError("webcam camera unavailable")
            self._capture = capture
            self._frame_no = 0
        elif not start:
            self._release()
        return webcam_status(start, consent)

    def snapshot(self, machine_id: str) -> dict[str, Any]:
        try:
            import cv2
        except RuntimeError as exc:
            raise ProviderError(str(exc)) from exc
        except ImportError as exc:
            raise ProviderError("opencv-python is not installed; webcam unavailable") from exc
        temporary = False
        capture = self._capture
        if capture is None:
            capture = cv2.VideoCapture(0)
            temporary = True
        try:
            ok, frame = capture.read()
            if not ok:
                raise ProviderError("webcam frame unavailable")
            self._frame_no += 1
            return encode_cv2_frame(frame, machine_id, self._frame_no)
        finally:
            if temporary:
                capture.release()

    def _release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None


class DemoInputController(InputController):
    def handle_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        return handle_input_event(payload)


class LocalSandboxRunner(SandboxRunner):
    async def run(self, machine_id: str, sandbox_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = payload["job_id"]
        cwd = job_sandbox(sandbox_root, machine_id, job_id)
        return await run_job(command_from_schema(payload), cwd, payload.get("timeout"))


class AgentProviders:
    def __init__(
        self,
        *,
        screen: ScreenCaptureProvider,
        processes: ProcessProvider,
        apps: AppLauncher,
        webcam: WebcamProvider,
        input_controller: InputController,
        sandbox: SandboxRunner,
    ) -> None:
        self.screen = screen
        self.processes = processes
        self.apps = apps
        self.webcam = webcam
        self.input_controller = input_controller
        self.sandbox = sandbox


def build_providers(mode: str) -> AgentProviders:
    if mode == "real":
        return AgentProviders(
            screen=RealScreenCaptureProvider(),
            processes=RealProcessProvider(),
            apps=RealAppLauncher(),
            webcam=RealWebcamProvider(),
            input_controller=DemoInputController(),
            sandbox=LocalSandboxRunner(),
        )
    return AgentProviders(
        screen=FakeScreenCaptureProvider(),
        processes=FakeProcessProvider(),
        apps=FakeAppLauncher(),
        webcam=FakeWebcamProvider(),
        input_controller=DemoInputController(),
        sandbox=LocalSandboxRunner(),
    )
