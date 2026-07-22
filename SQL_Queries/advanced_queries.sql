-- 19 Advanced SQL Queries for Retail Sales Analysis
-- Showcasing Window Functions, CTEs, RFM Analysis, and Pareto 80/20 Principles

-- 1. Customer RFM Analysis (Recency, Frequency, Monetary) Base CTE
WITH Customer_Stats AS (
    SELECT 
        customer_id,
        MAX(order_date) AS last_order_date,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(sales_amount) AS monetary_value
    FROM retail_sales
    GROUP BY customer_id
),
RFM_Scoring AS (
    SELECT 
        customer_id,
        last_order_date,
        frequency,
        monetary_value,
        NTILE(4) OVER(ORDER BY last_order_date ASC) AS R_Score,
        NTILE(4) OVER(ORDER BY frequency DESC) AS F_Score,
        NTILE(4) OVER(ORDER BY monetary_value DESC) AS M_Score
    FROM Customer_Stats
)
SELECT 
    customer_id,
    R_Score,
    F_Score,
    M_Score,
    (R_Score * 100) + (F_Score * 10) + M_Score AS RFM_Segment
FROM RFM_Scoring;

-- 2. Pareto Analysis (80/20 Rule) for Product Sales
WITH Product_Sales AS (
    SELECT 
        product_id,
        SUM(sales_amount) AS total_sales
    FROM retail_sales
    GROUP BY product_id
),
Running_Total AS (
    SELECT 
        product_id,
        total_sales,
        SUM(total_sales) OVER(ORDER BY total_sales DESC) AS cumulative_sales,
        SUM(total_sales) OVER() AS grand_total
    FROM Product_Sales
)
SELECT 
    product_id,
    total_sales,
    cumulative_sales,
    (cumulative_sales * 1.0 / grand_total) * 100 AS cumulative_percentage,
    CASE 
        WHEN (cumulative_sales * 1.0 / grand_total) <= 0.80 THEN 'Top 20% (80% Revenue)'
        ELSE 'Bottom 80%' 
    END AS pareto_category
FROM Running_Total;

-- 3. Customer Lifetime Value (CLV) Calculation
WITH Customer_Cohorts AS (
    SELECT 
        customer_id,
        MIN(DATE_TRUNC('month', order_date)) AS cohort_month
    FROM retail_sales
    GROUP BY customer_id
),
Cohort_Metrics AS (
    SELECT 
        c.cohort_month,
        COUNT(DISTINCT c.customer_id) AS initial_customers,
        SUM(s.sales_amount) AS total_cohort_revenue
    FROM Customer_Cohorts c
    JOIN retail_sales s ON c.customer_id = s.customer_id
    GROUP BY c.cohort_month
)
SELECT 
    cohort_month,
    initial_customers,
    total_cohort_revenue,
    (total_cohort_revenue / initial_customers) AS avg_clv_per_cohort
FROM Cohort_Metrics
ORDER BY cohort_month;

-- Note: This file contains a representative sample of the 19 advanced queries utilized for this project's analysis phase.
