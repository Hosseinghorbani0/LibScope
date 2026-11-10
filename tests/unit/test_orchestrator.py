import asyncio
from types import SimpleNamespace

import pytest
from libscope.api import orchestrator


def test_unexpected_analysis_error_is_sanitized_in_job_state(monkeypatch):
    states = []

    async def fail_analysis(*_args):
        raise RuntimeError("secret provider response")

    monkeypatch.setattr(orchestrator, "get_settings", lambda: SimpleNamespace(analysis_timeout_seconds=1))
    monkeypatch.setattr(orchestrator, "_run_package_analysis", fail_analysis)
    monkeypatch.setattr(orchestrator, "_finish_job", lambda *args: states.append(args))

    with pytest.raises(RuntimeError, match="secret provider response"):
        asyncio.run(orchestrator.run_package_analysis("sample", job_id="job-1"))

    assert states == [
        (
            "job-1",
            "failed",
            "Analysis failed.",
            "Analysis failed unexpectedly. Please retry or inspect service logs.",
        )
    ]


def test_analysis_timeout_marks_job_failed(monkeypatch):
    states = []

    async def slow_analysis(*_args):
        await asyncio.sleep(0.1)

    monkeypatch.setattr(orchestrator, "get_settings", lambda: SimpleNamespace(analysis_timeout_seconds=0.01))
    monkeypatch.setattr(orchestrator, "_run_package_analysis", slow_analysis)
    monkeypatch.setattr(orchestrator, "_finish_job", lambda *args: states.append(args))

    with pytest.raises(TimeoutError):
        asyncio.run(orchestrator.run_package_analysis("sample", job_id="job-2"))

    assert states == [
        (
            "job-2",
            "failed",
            "Analysis timed out.",
            "Analysis exceeded the configured time limit. Please retry.",
        )
    ]


def test_cancelled_analysis_marks_job_cancelled(monkeypatch):
    states = []

    async def waiting_analysis(*_args):
        await asyncio.Event().wait()

    monkeypatch.setattr(orchestrator, "get_settings", lambda: SimpleNamespace(analysis_timeout_seconds=1))
    monkeypatch.setattr(orchestrator, "_run_package_analysis", waiting_analysis)
    monkeypatch.setattr(orchestrator, "_finish_job", lambda *args: states.append(args))

    async def cancel_analysis():
        task = asyncio.create_task(orchestrator.run_package_analysis("sample", job_id="job-3"))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel_analysis())
    assert states == [("job-3", "cancelled", "Analysis was cancelled.", None)]

