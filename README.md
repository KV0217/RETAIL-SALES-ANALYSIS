# 🛒 Retail Sales Revenue Prediction

End-to-end retail analytics project combining order-level regression, time series forecasting, and SQL analytics on Superstore data. Uses XGBoost Regressor for order-level prediction, Facebook Prophet for 90-day revenue forecasting, ARIMA for statistical decomposition, and LSTM for deep learning forecasting — all compared side by side.

## 🔍 What Makes This Unique
- **Three-Layer Forecasting** — XGBoost (order level) + Prophet (90-day) + ARIMA (decomposition) + LSTM (deep learning) — four approaches compared on same dataset
- **SQL Analytics** — 19 SQL queries covering Basic → Advanced Window Functions, RFM segmentation, CLV, Pareto analysis, MoM/YoY growth
- **Pareto Analysis** — identifies which 20% of sub-categories drive 80% of revenue with running cumulative window
- **What-If Discount Analysis** — shows optimal discount level for maximum predicted revenue
- **Seasonality Decomposition** — trend + seasonality + residual breakdown via ARIMA and Prophet components
- **RFM Segmentation** — fully written in SQL using NTILE window function
- **Business Insights** — automated recommendations from SQL results including loss-making products and discount impact

## 📊 Dataset
Superstore Sales — 9,994 orders × 21 columns
Sales · Profit · Discount · Quantity · Category · Region · Segment

## 🛠️ Tech Stack
Python · XGBoost · Scikit-learn · Facebook Prophet · Statsmodels (ARIMA) · TensorFlow/Keras (LSTM) · SHAP · SQLite · Matplotlib · Seaborn

## 📁 Project Structure
| File | Description |
|------|-------------|
| `retail-sales-revenue.ipynb` | Full notebook |
| `requirements.txt` | Dependencies |

## 🔍 Key Sections
| # | Section | What it does |
|---|---------|-------------|
Libraries + Load Data | Superstore CSV + SQLite setup |
SQL Analytics | 19 queries — KPIs, RFM, CLV, Pareto, YoY |
SQL Visualizations | 6 charts from SQL query results |
Business Insights | Auto-generated recommendations from SQL |
EDA | Revenue by category, region, segment, trend |
Feature Engineering | ShipDays · IsQ4 · IsHighSeason · DiscountImpact |
Model Comparison | Linear · Ridge · Lasso · RF · GB · XGBoost |
Actual vs Predicted | Scatter + residuals plot |
Hyperparameter Tuning | RandomizedSearchCV on XGBoost |
SHAP | Feature importance + beeswarm |
Pareto Analysis | 80/20 revenue rule + top customers |
What-If Analysis | Discount level vs predicted revenue |
Prediction System | Interactive menu — single / batch / examples |
Category × Region Heatmap | Revenue by combination |
Seasonality Analysis | Monthly + quarterly + YoY trends |
Prophet Forecast | 90-day forecast + confidence intervals |
ARIMA Forecast | Stationarity test + decomposition + 3-month forecast |
LSTM Forecast | Deep learning time series forecasting |
Model Comparison | Prophet vs ARIMA vs LSTM side-by-side |

## 📈 Regression Results
| Model | Metric |
|-------|--------|
| Linear Regression | Baseline |
| Ridge Regression | Regularized |
| Random Forest | ~R² 0.XX |
| Gradient Boosting | ~R² 0.XX |
| **XGBoost (Tuned)** | **Best R²** |

## 🗄️ SQL Highlights
```sql
-- RFM Segmentation (NTILE + 3-level CTE)
WITH rfm AS (
    SELECT Customer_ID, MAX(Order_Date) AS last_order,
           COUNT(DISTINCT Order_ID) AS frequency,
           ROUND(SUM(Sales),0) AS monetary
    FROM superstore GROUP BY Customer_ID
),
scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY last_order DESC) AS recency_score,
        NTILE(5) OVER (ORDER BY frequency DESC)   AS frequency_score,
        NTILE(5) OVER (ORDER BY monetary DESC)    AS monetary_score
    FROM rfm
)
SELECT CASE WHEN recency_score>=4 AND frequency_score>=4
             AND monetary_score>=4 THEN '🏆 Champions'
            WHEN recency_score<=2 AND frequency_score<=2
            THEN '😴 At Risk' ELSE '📦 Regular' END AS rfm_segment,
       COUNT(*) AS customers
FROM scored GROUP BY rfm_segment
```

## 🔑 Key Insights
- Heavy discounting (40%+) results in negative profit margins
- Technology category drives highest average order value
- Q4 (Nov-Dec) is consistently the peak revenue quarter
- West region has highest total revenue
- 3-4 sub-categories drive ~80% of total revenue (Pareto)

## 💡 Forecasting Comparison
| Model | Type | Best For |
|-------|------|----------|
| XGBoost | Regression | Order-level prediction |
| Prophet | Time Series | Long-term trend + seasonality |
| ARIMA | Statistical | Short-term + decomposition |
| LSTM | Deep Learning | Complex sequential patterns |

## 👤 Author
**KAVIN VENKAT**
[LinkedIn](www.linkedin.com/in/kavin-venkat-1710s0202) 
