from __future__ import annotations

import os
import pty
import select
import shutil
import subprocess
import time

from rig.adapters.exec import AgentCommandNotFoundError, AgentResult, ExecAdapter
from rig.config import AgentConfig
from rig.run_context import RunContext


class PtyAdapter(ExecAdapter):
    def __init__(self, name: str, config: AgentConfig) -> None:
        super().__init__(name, config)

    def run(self, context: RunContext) -> AgentResult:
        command = self.build_command(context)
        if shutil.which(command[0]) is None:
            raise AgentCommandNotFoundError(
                f"Agent command was not found on PATH: {command[0]}\n"
                "Install the command or update .rig/config.yaml."
            )

        master_fd, slave_fd = pty.openpty()
        output = bytearray()
        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(
                command,
                cwd=context.execution_cwd,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                close_fds=True,
            )
            os.close(slave_fd)
            slave_fd = -1
            deadline = time.monotonic() + self.config.timeout_seconds
            timed_out = False

            while True:
                if process.poll() is not None:
                    output.extend(read_available(master_fd))
                    break
                if time.monotonic() >= deadline:
                    timed_out = True
                    process.kill()
                    process.wait()
                    output.extend(read_available(master_fd))
                    break

                readable, _, _ = select.select([master_fd], [], [], 0.1)
                if readable:
                    output.extend(read_available(master_fd))

            transcript = output.decode("utf-8", errors="replace")
            if timed_out:
                stderr = (
                    f"Rig PTY runner timed out after {self.config.timeout_seconds} seconds.\n"
                )
                return AgentResult(exit_code=124, stdout=transcript, stderr=stderr)

            return AgentResult(
                exit_code=process.returncode if process.returncode is not None else 1,
                stdout=transcript,
                stderr="",
            )
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            if slave_fd != -1:
                os.close(slave_fd)
            os.close(master_fd)


def read_available(fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        chunks.append(chunk)
        readable, _, _ = select.select([fd], [], [], 0)
        if not readable:
            break
    return b"".join(chunks)
