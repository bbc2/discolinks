from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

import rich.console
import rich.status

from . import outcome


@dataclass
class Stats:
    queued: int = 0
    in_progress: int = 0
    finished: int = 0
    ok: int = 0
    failed: int = 0

    def on_task_started(self, queued: int) -> None:
        self.queued = queued
        self.in_progress += 1

    def on_task_done(self, queued: int, result: outcome.Result) -> None:
        self.queued = queued
        self.in_progress -= 1
        self.finished += 1
        if result.ok():
            self.ok += 1
        else:
            self.failed += 1


@dataclass(frozen=True)
class Monitor:
    """
    Handle updates of the status bar during scraping.

    Create an instance with `start` and finish the execution with `stop`.
    """

    console: rich.console.Console
    status: rich.status.Status
    stats: Stats = field(init=False, default_factory=Stats)

    @classmethod
    def start(cls, console: rich.console.Console) -> "Monitor":
        status = rich.status.Status(status="Working", console=console)
        status.start()
        return cls(console=console, status=status)

    def print(self, msg: str) -> None:
        self.console.print(msg, markup=False, emoji=False)

    def _update_status(self) -> None:
        self.status.update(
            f"Working:"
            f" [bold blue]{self.stats.queued} [dim white]queued"
            f" → [not dim][bold yellow]{self.stats.in_progress} [dim white]in progress"
            f" → [not dim][bold white]{self.stats.finished} [dim white]finished"
            f" ([not dim][bold green]{self.stats.ok} [dim white]ok,"
            f" [not dim][bold red]{self.stats.failed} [dim white]failed)"
        )

    def on_task_start(self, queued: int) -> None:
        self.stats.on_task_started(queued=queued)
        self._update_status()

    def on_task_done(self, result: outcome.Result, queued: int) -> None:
        self.stats.on_task_done(queued=queued, result=result)
        self._update_status()

    def stop(self) -> None:
        self.status.stop()


@contextmanager
def new_monitor(console: rich.console.Console) -> Iterator[Monitor]:
    """
    Yield a `Monitor` instance and ensure it is stopped properly.
    """

    monitor = Monitor.start(console=console)
    try:
        yield monitor
    finally:
        monitor.stop()
