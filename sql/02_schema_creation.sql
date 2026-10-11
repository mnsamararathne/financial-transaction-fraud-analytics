-- ============================================================
-- Financial Transaction Fraud Analytics
-- Schema Creation
-- ============================================================

-- RAW
-- Stores data in its original imported form.
CREATE SCHEMA IF NOT EXISTS raw;

-- STAGING
-- Used for validation, cleaning and transformation.
CREATE SCHEMA IF NOT EXISTS staging;

-- WAREHOUSE
-- Stores analytical fact and dimension tables.
CREATE SCHEMA IF NOT EXISTS warehouse;

-- ANALYTICS
-- Stores reporting views, materialized views and analytical
-- datasets used by Python and Power BI.
CREATE SCHEMA IF NOT EXISTS analytics;
