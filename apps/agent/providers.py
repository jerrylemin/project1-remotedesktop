from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from apps.agent.app_manager import list_applications, start_application
from apps.agent.input_demo import handle_input_event
from apps.agent.job_runner import run_job
from apps.agent.process_manager import list_processes, stop_process
from apps.agent.sandbox import job_sandbox
from apps.agent.screen import fake_jpeg_frame, real_jpeg_frame
from apps.agent.webcam import webcam_status


class ProviderError(RuntimeError):
    pass


class ScreenCaptureProvider(ABC):
    @abstractmethod
    def capture_jpeg_b64(self) -> str:
        raise NotImplementedError


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


class WebcamProvider(ABC):
    @abstractmethod
    def set_webcam(self, start: bool, consent: bool) -> dict[str, Any]:
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


class RealAppLauncher(AppLauncher):
    def list_applications(self) -> list[dict[str, Any]]:
        return list_applications()

    def start_application(self, command: str) -> dict[str, Any]:
        return start_application(command)


class FakeWebcamProvider(WebcamProvider):
    def set_webcam(self, start: bool, consent: bool) -> dict[str, Any]:
        if start and not consent:
            raise ProviderError("webcam requires explicit consent")
        return {"webcam": "started" if start else "stopped", "fake": True}


class RealWebcamProvider(WebcamProvider):
    def set_webcam(self, start: bool, consent: bool) -> dict[str, Any]:
        try:
            import cv2  # noqa: F401
        except ImportError as exc:
            raise ProviderError("opencv-python is not installed; webcam unavailable") from exc
        return webcam_status(start, consent)


class DemoInputController(InputController):
    def handle_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        return handle_input_event(payload)


class LocalSandboxRunner(SandboxRunner):
    async def run(self, machine_id: str, sandbox_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = payload["job_id"]
        cwd = job_sandbox(sandbox_root, machine_id, job_id)
        return await run_job(payload["command"], cwd, payload.get("timeout"))


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

