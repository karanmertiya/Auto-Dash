import polars as pl

from app.modules.profiling.service import DatasetProfiler


def test_profiler_detects_roles_and_quality_signals() -> None:
    df = pl.DataFrame(
        {
            "order_id": ["A1", "A2", "A2", "A4"],
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-02", None],
            "revenue": [100.0, 125.5, 125.5, 9999.0],
            "region": ["North", "South", "South", None],
        }
    )

    profile = DatasetProfiler().profile(df)
    roles = {column.name: column.semantic_role for column in profile.columns}

    assert profile.row_count == 4
    assert profile.duplicate_row_count == 2
    assert roles["order_id"] == "id"
    assert roles["order_date"] == "date"
    assert roles["revenue"] == "metric"
    assert roles["region"] == "dimension"
    assert any(column.name == "region" and column.stats.missing_count == 1 for column in profile.columns)
