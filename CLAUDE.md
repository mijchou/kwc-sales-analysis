# Sales Analysis Dashboard

A Streamlit-based sales analytics application for analyzing sales transactions, customer behavior, and product performance.

## Docker Environment

This project runs inside a Docker container. Key implications:
- File paths use `/app/` as the root (e.g., `/app/static/` for images)
- The Streamlit app is accessed via mapped port (typically 8502)
- When referencing static assets (images), use paths relative to `/app/`

## Project Structure

- `streamlit_app.py` - Main app entry point, handles navigation and sidebar filters
- `kwc_dashboard.py` - New KWC Sales Dashboard (default landing page)
- `dashboard_utils.py` - Helper functions for dashboard metrics and calculations
- `sales_overview.py` - Overview page with summary metrics and top-level analytics (legacy)
- `customer_analysis.py` - Customer detail page showing individual customer sales over time (legacy)
- `sales_analysis.py` - Sales analysis functionality (legacy)
- `utils.py` - Utility functions for navigation and plotting

## Data

Data files are stored in `data/` directory:
- `data/sales/` - Sales transaction records
- `data/accounts/` - Customer account information
- `data/items/` - Product/item data

## Running the App

When you want to verify changes work correctly, ask the user to run the Streamlit app manually. Do not attempt to start it automatically.
