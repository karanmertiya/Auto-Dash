import pandas as pd
import polars as pl


def transform(df):
    result = df.clone()
    result = result.rename({'order date': 'order_date'})
    result = result.unique(maintain_order=True)
    result = result.with_columns([
        pl.col('order_date').cast(pl.String, strict=False).str.strptime(pl.Date, strict=False).alias('order_date'),
    ])
    result = result.with_columns([
        pl.col('revenue').cast(pl.Float64, strict=False).alias('revenue'),
        pl.col('cost').cast(pl.Float64, strict=False).alias('cost'),
        pl.col('units').cast(pl.Float64, strict=False).alias('units'),
    ])
    result = result.with_columns((pl.col('order_date').is_null() | pl.col('revenue').is_null() | pl.col('cost').is_null()).alias('_dashforge_review_flag'))
    return result
