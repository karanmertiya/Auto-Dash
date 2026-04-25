from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl

from app.modules.cleaning.safety import validate_transform_script

ALLOWED_BUILTINS: dict[str, Any] = {
    "abs": abs,
    "bool": bool,
    "dict": dict,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "round": round,
    "set": set,
    "str": str,
    "sum": sum,
    "tuple": tuple,
}


def main(job_path: str) -> int:
    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    try:
        tree = validate_transform_script(job["script"])
        namespace: dict[str, Any] = {
            "__builtins__": ALLOWED_BUILTINS,
            "pl": pl,
            "pd": pd,
        }
        exec(compile(tree, "<dashforge-cleaning-plan>", "exec"), namespace)
        df = pl.read_parquet(job["input_path"])
        result = namespace["transform"](df)
        if not isinstance(result, pl.DataFrame):
            raise TypeError("transform(df) must return a polars.DataFrame.")
        output_path = Path(job["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.write_parquet(output_path)
        response = {
            "status": "succeeded",
            "output_path": str(output_path),
            "preview_rows": result.head(50).to_dicts(),
            "row_count": result.height,
            "columns": result.columns,
        }
    except Exception as exc:  # noqa: BLE001 - runner must serialize all failures.
        response = {
            "status": "failed",
            "error_message": str(exc),
            "traceback": traceback.format_exc(limit=8),
        }
    Path(job["result_path"]).write_text(json.dumps(response, default=str), encoding="utf-8")
    return 0 if response["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))

