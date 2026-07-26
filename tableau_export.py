"""
Tableau Hyper Export — Retail Sales Revenue Prediction
======================================================
Exports RFM segmentation, profit margin analysis, and time-series
forecast results as a Tableau Hyper extract (.hyper) — the native
high-performance format for Tableau Desktop, Tableau Public, and
Tableau Server.

Three tables are written to a single .hyper file:
  1. RFM_Segments      — Customer segmentation (Champions, At Risk, etc.)
  2. Profit_Analysis   — Order-level profit margin vs model predictions
  3. Revenue_Forecast  — Weekly actual + predicted revenue with CI bands

Setup:
    pip install tableauhyperapi pandas numpy python-dotenv

Usage:
    python tableau_export.py
    Then: Tableau Desktop → File → Open → retail_sales_analysis.hyper

Note: tableauhyperapi requires Python 3.8–3.11 and a 64-bit system.
      Download: https://tableau.github.io/hyper-db/docs/
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from tableauhyperapi import (
    Connection,
    CreateMode,
    HyperProcess,
    Inserter,
    NOT_NULLABLE,
    NULLABLE,
    SqlType,
    TableDefinition,
    TableName,
    Telemetry,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("tableau_exports")
OUTPUT_DIR.mkdir(exist_ok=True)
HYPER_PATH = str(OUTPUT_DIR / "retail_sales_analysis.hyper")


# ── Table Schemas ─────────────────────────────────────────────────────────────

SCHEMA_RFM = TableDefinition(
    table_name=TableName("Extract", "RFM_Segments"),
    columns=[
        TableDefinition.Column("Customer_ID",       SqlType.text(),   NOT_NULLABLE),
        TableDefinition.Column("Segment",           SqlType.text(),   NOT_NULLABLE),
        TableDefinition.Column("Recency_Days",      SqlType.int(),    NOT_NULLABLE),
        TableDefinition.Column("Frequency",         SqlType.int(),    NOT_NULLABLE),
        TableDefinition.Column("Monetary_USD",      SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("RFM_Score",         SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("Churn_Risk",        SqlType.text(),   NOT_NULLABLE),
        TableDefinition.Column("CLV_Estimate_USD",  SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("Pareto_Group",      SqlType.text(),   NOT_NULLABLE),
    ],
)

SCHEMA_PROFIT = TableDefinition(
    table_name=TableName("Extract", "Profit_Analysis"),
    columns=[
        TableDefinition.Column("Order_Date",        SqlType.date(),   NOT_NULLABLE),
        TableDefinition.Column("Category",          SqlType.text(),   NOT_NULLABLE),
        TableDefinition.Column("Sub_Category",      SqlType.text(),   NOT_NULLABLE),
        TableDefinition.Column("Region",            SqlType.text(),   NOT_NULLABLE),
        TableDefinition.Column("Sales_USD",         SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("Profit_USD",        SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("Discount_Pct",      SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("Profit_Margin_Pct", SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("Predicted_Margin",  SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("Margin_Error",      SqlType.double(), NOT_NULLABLE),
    ],
)

SCHEMA_FORECAST = TableDefinition(
    table_name=TableName("Extract", "Revenue_Forecast"),
    columns=[
        TableDefinition.Column("Date",              SqlType.date(),   NOT_NULLABLE),
        TableDefinition.Column("Actual_Revenue",    SqlType.double(), NULLABLE),
        TableDefinition.Column("Predicted_Revenue", SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("Lower_CI_95",       SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("Upper_CI_95",       SqlType.double(), NOT_NULLABLE),
        TableDefinition.Column("Model",             SqlType.text(),   NOT_NULLABLE),
        TableDefinition.Column("Is_Forecast",       SqlType.bool(),   NOT_NULLABLE),
    ],
)


# ── Data Generators ───────────────────────────────────────────────────────────

def build_rfm_data(n: int = 500) -> pd.DataFrame:
    """
    Generate RFM-segmented customer data.
    In production: replace with output from your SQL RFM query.
    """
    np.random.seed(42)
    segments = [
        "Champions", "Loyal Customers", "Potential Loyalists",
        "At Risk", "Lost Customers", "New Customers",
    ]
    probs = [0.15, 0.20, 0.20, 0.20, 0.10, 0.15]
    churn_map = {
        "Champions": "Low",  "Loyal Customers": "Low",
        "Potential Loyalists": "Medium", "At Risk": "High",
        "Lost Customers": "Critical",    "New Customers": "Medium",
    }

    seg      = np.random.choice(segments, n, p=probs)
    recency  = np.random.randint(1, 365, n)
    freq     = np.random.randint(1, 50, n)
    monetary = np.round(np.random.exponential(500, n) + 20, 2)
    rfm_score = np.round((1 / (recency + 1)) * 100 + freq * 2 + monetary / 100, 2)
    clv      = np.round(monetary * freq * np.random.uniform(1.5, 3.5, n), 2)

    # Pareto 80/20: top 20% customers = "Pareto Top 20"
    cumsum   = np.cumsum(np.sort(monetary)[::-1])
    top20_thresh = monetary[np.argsort(monetary)[::-1][int(n * 0.2)]]
    pareto   = np.where(monetary >= top20_thresh, "Pareto Top 20%", "Remaining 80%")

    return pd.DataFrame({
        "Customer_ID":      [f"CUST_{i:05d}" for i in range(1, n + 1)],
        "Segment":          seg,
        "Recency_Days":     recency,
        "Frequency":        freq,
        "Monetary_USD":     monetary,
        "RFM_Score":        rfm_score,
        "Churn_Risk":       [churn_map[s] for s in seg],
        "CLV_Estimate_USD": clv,
        "Pareto_Group":     pareto,
    })


def build_profit_data(n: int = 2000) -> pd.DataFrame:
    """
    Order-level profit analysis matching Superstore dataset structure.
    In production: replace with your actual Superstore CSV loaded via Pandas.
    """
    np.random.seed(42)
    cats = {
        "Technology":      ["Phones", "Computers", "Accessories", "Copiers"],
        "Furniture":       ["Chairs", "Tables", "Bookcases", "Storage"],
        "Office Supplies": ["Binders", "Paper", "Pens", "Envelopes", "Labels"],
    }
    regions    = ["West", "East", "Central", "South"]
    base_margin = {"Technology": 0.18, "Furniture": 0.08, "Office Supplies": 0.22}
    start = datetime(2021, 1, 1)
    rows = []

    for _ in range(n):
        cat  = np.random.choice(list(cats.keys()))
        sub  = np.random.choice(cats[cat])
        reg  = np.random.choice(regions)
        sales     = round(abs(np.random.exponential(300)) + 10, 2)
        discount  = round(
            np.random.choice([0, 0.1, 0.2, 0.3, 0.4, 0.5],
                             p=[0.4, 0.2, 0.2, 0.1, 0.07, 0.03]), 2
        )
        margin    = round(base_margin[cat] - discount * 0.8 + np.random.normal(0, 0.03), 4)
        profit    = round(sales * margin, 2)
        pred_margin = round(margin + np.random.normal(0, 0.01), 4)
        error       = round(abs(margin - pred_margin) * 100, 4)
        days = int(np.random.uniform(0, 1460))
        order_date  = (start + pd.Timedelta(days=days)).date()
        rows.append([
            order_date, cat, sub, reg,
            sales, profit, discount,
            round(margin * 100, 2),
            round(pred_margin * 100, 2),
            error,
        ])

    return pd.DataFrame(rows, columns=[
        "Order_Date", "Category", "Sub_Category", "Region",
        "Sales_USD", "Profit_USD", "Discount_Pct",
        "Profit_Margin_Pct", "Predicted_Margin", "Margin_Error",
    ])


def build_forecast_data(weeks: int = 156, forecast_horizon: int = 26) -> pd.DataFrame:
    """
    Weekly revenue forecast: actual (historical) + predicted (future) + 95% CI.
    In production: replace with Prophet/ARIMA/XGBoost ensemble output.
    """
    np.random.seed(42)
    dates    = pd.date_range("2021-01-01", periods=weeks, freq="W-MON")
    trend    = np.linspace(5000, 12000, weeks)
    seasonal = 1500 * np.sin(np.linspace(0, 4 * np.pi, weeks))
    noise    = np.random.normal(0, 300, weeks)
    actual   = trend + seasonal + noise

    split = weeks - forecast_horizon
    rows  = []
    for i, d in enumerate(dates):
        is_fc    = i >= split
        pred     = trend[i] + seasonal[i] + np.random.normal(0, 150)
        ci_width = 400 + i * 2.5
        rows.append([
            d.date(),
            None if is_fc else round(float(actual[i]), 2),
            round(float(pred), 2),
            round(float(pred - ci_width), 2),
            round(float(pred + ci_width), 2),
            "XGBoost + Prophet Ensemble",
            bool(is_fc),
        ])

    return pd.DataFrame(rows, columns=[
        "Date", "Actual_Revenue", "Predicted_Revenue",
        "Lower_CI_95", "Upper_CI_95", "Model", "Is_Forecast",
    ])


# ── Hyper Writer ──────────────────────────────────────────────────────────────

def export_to_hyper(output_path: str = HYPER_PATH) -> str:
    """
    Write all three datasets to a single multi-table Tableau Hyper extract.
    Open in Tableau Desktop: File → Open → retail_sales_analysis.hyper
    """
    logger.info(f"Building Tableau Hyper extract → {output_path}")

    rfm_df      = build_rfm_data()
    profit_df   = build_profit_data()
    forecast_df = build_forecast_data()

    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(
            endpoint=hyper.endpoint,
            database=output_path,
            create_mode=CreateMode.CREATE_AND_REPLACE,
        ) as conn:
            conn.catalog.create_schema_if_not_exists("Extract")

            # ── RFM Segments ──────────────────────────────────────────────────
            conn.catalog.create_table_if_not_exists(SCHEMA_RFM)
            with Inserter(conn, SCHEMA_RFM) as ins:
                for _, r in rfm_df.iterrows():
                    ins.add_row([
                        r.Customer_ID, r.Segment,
                        int(r.Recency_Days), int(r.Frequency),
                        float(r.Monetary_USD), float(r.RFM_Score),
                        r.Churn_Risk, float(r.CLV_Estimate_USD),
                        r.Pareto_Group,
                    ])
                ins.execute()
            logger.info(f"  RFM_Segments: {len(rfm_df):,} rows")

            # ── Profit Analysis ───────────────────────────────────────────────
            conn.catalog.create_table_if_not_exists(SCHEMA_PROFIT)
            with Inserter(conn, SCHEMA_PROFIT) as ins:
                for _, r in profit_df.iterrows():
                    ins.add_row([
                        r.Order_Date, r.Category, r.Sub_Category, r.Region,
                        float(r.Sales_USD), float(r.Profit_USD),
                        float(r.Discount_Pct), float(r.Profit_Margin_Pct),
                        float(r.Predicted_Margin), float(r.Margin_Error),
                    ])
                ins.execute()
            logger.info(f"  Profit_Analysis: {len(profit_df):,} rows")

            # ── Revenue Forecast ──────────────────────────────────────────────
            conn.catalog.create_table_if_not_exists(SCHEMA_FORECAST)
            with Inserter(conn, SCHEMA_FORECAST) as ins:
                for _, r in forecast_df.iterrows():
                    ins.add_row([
                        r.Date,
                        None if pd.isna(r.Actual_Revenue) else float(r.Actual_Revenue),
                        float(r.Predicted_Revenue),
                        float(r.Lower_CI_95), float(r.Upper_CI_95),
                        r.Model, bool(r.Is_Forecast),
                    ])
                ins.execute()
            logger.info(f"  Revenue_Forecast: {len(forecast_df):,} rows")

    logger.info(f"Hyper extract complete → {output_path}")
    return output_path


def export_csv_fallback() -> None:
    """Export plain CSVs as a fallback for Tableau Public users."""
    build_rfm_data().to_csv(OUTPUT_DIR / "rfm_segments.csv", index=False)
    build_profit_data().to_csv(OUTPUT_DIR / "profit_analysis.csv", index=False)
    build_forecast_data().to_csv(OUTPUT_DIR / "revenue_forecast.csv", index=False)
    logger.info(f"CSV fallbacks saved → {OUTPUT_DIR}/")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 58)
    print("  Tableau Hyper Export — Retail Sales Revenue Analysis")
    print("=" * 58)

    hyper_path = export_to_hyper()
    export_csv_fallback()

    print(f"\nHyper extract → {hyper_path}")
    print(f"CSV fallbacks → {OUTPUT_DIR}/")
    print("\nTo open in Tableau Desktop:")
    print("  File → Open → retail_sales_analysis.hyper")
    print("\nTo publish to Tableau Server/Online:")
    print("  import tableauserverclient as TSC")
    print("  # See: https://tableau.github.io/server-client-python/")
