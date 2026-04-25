from __future__ import annotations

import json
import subprocess
import sys
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.modules.cleaning.safety import validate_transform_script
from app.modules.cleaning.schemas import CleaningExecutionResult


class SafeScriptExecutor:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def execute(self, *, script: str, input_path: str, execution_id: str | None = None) -> CleaningExecutionResult:
        validate_transform_script(script)
        execution_id = execution_id or str(uuid4())
        execution_dir = self.settings.storage_dir / "executions" / execution_id
        execution_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.settings.storage_dir / "cleaned" / f"{execution_id}.parquet"
        result_path = execution_dir / "result.json"
        job_path = execution_dir / "job.json"
        job_path.write_text(
            json.dumps(
                {
                    "script": script,
                    "input_path": input_path,
                    "output_path": str(output_path),
                    "result_path": str(result_path),
                }
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, "-m", "app.modules.cleaning.runner", str(job_path)],
            cwd=self.settings.app_root,
            capture_output=True,
            text=True,
            timeout=self.settings.script_timeout_seconds,
            check=False,
        )
        run_log = {
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
            "job_path": str(job_path),
        }
        if not result_path.exists():
            return CleaningExecutionResult(
                status="failed",
                error_message="Cleaning runner did not produce a result file.",
                attempts=1,
                run_log=run_log,
            )
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        if payload["status"] == "succeeded":
            return CleaningExecutionResult(
                status="succeeded",
                output_path=payload["output_path"],
                preview_rows=payload.get("preview_rows", []),
                attempts=1,
                run_log={**run_log, "row_count": payload.get("row_count"), "columns": payload.get("columns")},
            )
        return CleaningExecutionResult(
            status="failed",
            error_message=payload.get("error_message", "Unknown script failure."),
            attempts=1,
            run_log={**run_log, "traceback": payload.get("traceback")},
        )

