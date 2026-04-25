from __future__ import annotations

from math import isfinite
from typing import Any

import polars as pl

from app.modules.profiling.schemas import (
    ColumnProfileModel,
    ColumnStats,
    DatasetProfileModel,
    DatasetSchemaModel,
    RelationshipHint,
    SemanticRole,
)


class DatasetProfiler:
    def profile(self, df: pl.DataFrame, dataset_id: str | None = None, version_id: str | None = None) -> DatasetProfileModel:
        duplicate_count = int(df.is_duplicated().sum()) if df.height else 0
        columns = [self._profile_column(df, column) for column in df.columns]
        warnings: list[str] = []
        if duplicate_count:
            warnings.append(f"{duplicate_count} duplicate rows detected.")
        if not df.height:
            warnings.append("Dataset has zero rows.")
        return DatasetProfileModel(
            dataset_id=dataset_id,
            version_id=version_id,
            row_count=df.height,
            column_count=len(df.columns),
            duplicate_row_count=duplicate_count,
            columns=columns,
            relationship_hints=self._relationship_hints(columns),
            warnings=warnings,
        )

    def schema_from_profile(self, profile: DatasetProfileModel) -> DatasetSchemaModel:
        role_map = {column.name: column.semantic_role for column in profile.columns}
        return DatasetSchemaModel(
            columns={column.name: column.inferred_type for column in profile.columns},
            role_map=role_map,
            candidate_ids=[name for name, role in role_map.items() if role == "id"],
            candidate_dates=[name for name, role in role_map.items() if role == "date"],
            candidate_metrics=[name for name, role in role_map.items() if role == "metric"],
            candidate_dimensions=[name for name, role in role_map.items() if role == "dimension"],
        )

    def _profile_column(self, df: pl.DataFrame, column: str) -> ColumnProfileModel:
        series = df[column]
        row_count = df.height
        missing_count = int(series.null_count())
        distinct_count = int(series.n_unique()) if row_count else 0
        inferred_type = str(series.dtype)
        semantic_role = self._semantic_role(column, series, row_count, distinct_count)
        stats = ColumnStats(
            row_count=row_count,
            missing_count=missing_count,
            missing_ratio=round(missing_count / row_count, 6) if row_count else 0,
            distinct_count=distinct_count,
            cardinality_ratio=round(distinct_count / row_count, 6) if row_count else 0,
            sample_values=self._sample_values(series),
            numeric=self._numeric_stats(series),
            temporal=self._temporal_stats(series),
            text=self._text_stats(series),
            mixed_type_signals=self._mixed_type_signals(series),
        )
        warnings = self._column_warnings(column, stats, semantic_role)
        return ColumnProfileModel(
            name=column,
            inferred_type=inferred_type,
            semantic_role=semantic_role,
            stats=stats,
            warnings=warnings,
        )

    def _semantic_role(
        self, column: str, series: pl.Series, row_count: int, distinct_count: int
    ) -> SemanticRole:
        lower = column.lower()
        cardinality_ratio = distinct_count / row_count if row_count else 0
        dtype = series.dtype
        if ("id" == lower or lower.endswith("_id") or lower.endswith(" id")) and cardinality_ratio > 0.6:
            return "id"
        if dtype in (pl.Date, pl.Datetime, pl.Time) or any(token in lower for token in ("date", "time", "month")):
            return "date"
        if dtype.is_numeric():
            if "id" in lower and cardinality_ratio > 0.6:
                return "id"
            return "metric"
        if dtype == pl.Boolean:
            return "dimension"
        if dtype == pl.String:
            avg_len = self._average_string_length(series)
            if avg_len > 40:
                return "text"
            if cardinality_ratio <= 0.5 or distinct_count <= 50:
                return "dimension"
        return "unknown"

    def _numeric_stats(self, series: pl.Series) -> dict[str, float | int | None]:
        if not series.dtype.is_numeric():
            return {}
        clean = series.drop_nulls()
        if clean.is_empty():
            return {"min": None, "max": None, "mean": None, "median": None, "outlier_count": 0}
        q1 = clean.quantile(0.25)
        q3 = clean.quantile(0.75)
        iqr = (q3 - q1) if q1 is not None and q3 is not None else 0
        outlier_count = 0
        if iqr and isfinite(float(iqr)):
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_count = int(((clean < lower) | (clean > upper)).sum())
        return {
            "min": self._safe_float(clean.min()),
            "max": self._safe_float(clean.max()),
            "mean": self._safe_float(clean.mean()),
            "median": self._safe_float(clean.median()),
            "q1": self._safe_float(q1),
            "q3": self._safe_float(q3),
            "outlier_count": outlier_count,
        }

    def _temporal_stats(self, series: pl.Series) -> dict[str, str | None]:
        if series.dtype not in (pl.Date, pl.Datetime):
            parsed = self._parse_datetime_series(series)
            if parsed is None:
                return {}
            non_null_ratio = float(parsed.is_not_null().mean() or 0)
            if non_null_ratio < 0.6:
                return {}
            date_series = parsed.drop_nulls()
        else:
            date_series = series.drop_nulls()
        if date_series.is_empty():
            return {"min": None, "max": None}
        return {"min": str(date_series.min()), "max": str(date_series.max())}

    def _text_stats(self, series: pl.Series) -> dict[str, float | int | None]:
        if series.dtype != pl.String:
            return {}
        lengths = series.drop_nulls().str.len_chars()
        if lengths.is_empty():
            return {"avg_length": 0, "max_length": 0}
        return {
            "avg_length": self._safe_float(lengths.mean()),
            "max_length": int(lengths.max() or 0),
        }

    def _mixed_type_signals(self, series: pl.Series) -> dict[str, float]:
        as_text = series.cast(pl.String, strict=False).drop_nulls()
        if as_text.is_empty():
            return {}
        numeric_ratio = float(as_text.cast(pl.Float64, strict=False).is_not_null().mean() or 0)
        parsed_dates = self._parse_datetime_series(series)
        date_ratio = float(parsed_dates.is_not_null().mean() or 0) if parsed_dates is not None else 0
        return {
            "parseable_numeric_ratio": round(numeric_ratio, 6),
            "parseable_datetime_ratio": round(date_ratio, 6),
        }

    def _column_warnings(
        self, column: str, stats: ColumnStats, semantic_role: SemanticRole
    ) -> list[str]:
        warnings: list[str] = []
        if stats.missing_ratio > 0.2:
            warnings.append(f"{column} has {stats.missing_ratio:.1%} missing values.")
        if semantic_role == "id" and stats.cardinality_ratio < 0.95:
            warnings.append(f"{column} looks like an identifier but is not unique.")
        if stats.numeric.get("outlier_count", 0):
            warnings.append(f"{column} has {stats.numeric['outlier_count']} IQR outliers.")
        if (
            stats.mixed_type_signals.get("parseable_numeric_ratio", 0) > 0.2
            and stats.mixed_type_signals.get("parseable_numeric_ratio", 0) < 0.95
        ):
            warnings.append(f"{column} has mixed numeric-like and non-numeric values.")
        return warnings

    def _relationship_hints(self, columns: list[ColumnProfileModel]) -> list[RelationshipHint]:
        hints: list[RelationshipHint] = []
        for column in columns:
            if column.semantic_role == "id":
                hints.append(
                    RelationshipHint(
                        left_column=column.name,
                        confidence=0.65 if column.stats.cardinality_ratio >= 0.95 else 0.45,
                        rationale="Identifier-like name and high cardinality suggest a join key candidate.",
                    )
                )
        return hints

    def _sample_values(self, series: pl.Series) -> list[Any]:
        values: list[Any] = []
        for item in series.drop_nulls().head(5).to_list():
            values.append(item.isoformat() if hasattr(item, "isoformat") else item)
        return values

    def _average_string_length(self, series: pl.Series) -> float:
        if series.dtype != pl.String:
            return 0
        lengths = series.drop_nulls().str.len_chars()
        return float(lengths.mean() or 0)

    def _parse_datetime_series(self, series: pl.Series) -> pl.Series | None:
        as_text = series.cast(pl.String, strict=False)
        best: pl.Series | None = None
        best_count = -1
        for fmt in (None, "%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = (
                    as_text.str.strptime(pl.Datetime, strict=False)
                    if fmt is None
                    else as_text.str.strptime(pl.Datetime, format=fmt, strict=False)
                )
            except Exception:
                continue
            parsed_count = int(parsed.is_not_null().sum())
            if parsed_count > best_count:
                best = parsed
                best_count = parsed_count
        return best

    def _safe_float(self, value: Any) -> float | None:
        if value is None:
            return None
        numeric = float(value)
        return numeric if isfinite(numeric) else None
