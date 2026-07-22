# Retail Sales Revenue Prediction

## Overview
End-to-End Machine Learning and Analytics project predicting retail sales revenue. 
Achieved an R2 of 0.9436 and RMSE of $0.10 via a 4-model ensemble.

*Note: The FastAPI deployment for this model is available in the [Sales-Profit-API](https://github.com/KV0217/Sales-Profit-API) repository.*

## Key Features
- **Predictive Modeling:** 4-model ensemble leveraging XGBoost, Prophet, ARIMA, and LSTM.
- **Explainability:** SHAP values to explain complex model behaviors.
- **Advanced SQL Analytics:** Includes 19 advanced SQL queries implementing RFM (Recency, Frequency, Monetary) analysis, CLV (Customer Lifetime Value), and Pareto (80/20) analysis.

## Tech Stack
- **Languages:** Python, SQL
- **Machine Learning & Time Series:** XGBoost, Prophet, ARIMA, LSTM, SHAP
- **Database:** SQLite

## Business Value
Provides robust sales forecasts and advanced customer segmentation. Connects to a "What-If" API that quantifies real-time margin changes based on discount strategies.
