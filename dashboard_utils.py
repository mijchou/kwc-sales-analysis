"""
Dashboard utility functions for KWC Sales Dashboard.
Provides calculation helpers for metrics, period comparisons, and customer segmentation.
"""
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


# Area code to region name mapping (South Africa + neighboring countries)
AREA_CODE_MAP = {
    10: 'Gauteng',
    11: 'Gauteng',
    12: 'Gauteng',
    13: 'Mpumalanga',
    14: 'North West',
    15: 'Limpopo',
    16: 'Gauteng',
    17: 'Mpumalanga',
    18: 'North West',
    21: 'Western Cape',
    22: 'Western Cape',
    23: 'Western Cape',
    27: 'Western Cape',
    28: 'Western Cape',
    31: 'KwaZulu-Natal',
    32: 'KwaZulu-Natal',
    33: 'KwaZulu-Natal',
    34: 'KwaZulu-Natal',
    35: 'KwaZulu-Natal',
    36: 'KwaZulu-Natal',
    39: 'KwaZulu-Natal',
    40: 'Eastern Cape',
    41: 'Eastern Cape',
    42: 'Eastern Cape',
    43: 'Eastern Cape',
    44: 'Western Cape',
    45: 'Eastern Cape',
    46: 'Eastern Cape',
    47: 'Eastern Cape',
    48: 'Free State',
    49: 'Eastern Cape',
    51: 'Free State',
    53: 'Northern Cape',
    54: 'Northern Cape',
    56: 'Free State',
    57: 'Free State',
    58: 'Free State',
    87: 'Gauteng',
    267: 'Botswana',
    264: 'Namibia',
    268: 'Eswatini',
    266: 'Lesotho',
}


def get_region_name(area_code):
    """Map area code to region name."""
    if pd.isna(area_code):
        return 'Unknown'
    try:
        code = int(float(area_code))
        return AREA_CODE_MAP.get(code, 'Other')
    except (ValueError, TypeError):
        return 'Unknown'


def format_currency(value, prefix='R '):
    """Format value as South African Rand."""
    if pd.isna(value):
        return f'{prefix}0'
    if abs(value) >= 1_000_000:
        return f'{prefix}{value/1_000_000:.1f}M'
    elif abs(value) >= 1_000:
        return f'{prefix}{value/1_000:.1f}K'
    else:
        return f'{prefix}{value:,.0f}'


def format_number(value):
    """Format number with thousands separator."""
    if pd.isna(value):
        return '0'
    if abs(value) >= 1_000_000:
        return f'{value/1_000_000:.1f}M'
    elif abs(value) >= 1_000:
        return f'{value/1_000:.1f}K'
    else:
        return f'{value:,.0f}'


def format_percentage(value, decimal_places=1):
    """Format value as percentage."""
    if pd.isna(value):
        return '0%'
    return f'{value:.{decimal_places}f}%'


def calculate_delta(current, previous):
    """Calculate percentage change between two values."""
    if previous == 0 or pd.isna(previous):
        if current > 0:
            return 100.0
        return 0.0
    return ((current - previous) / abs(previous)) * 100


def get_comparison_period(start_date, end_date, comparison_type='previous'):
    """
    Get comparison period dates.

    comparison_type:
        'previous' - Same duration, immediately before
        'yoy' - Same period, previous year
    """
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)

    duration = (end_date - start_date).days + 1

    if comparison_type == 'yoy':
        prev_start = start_date - relativedelta(years=1)
        prev_end = end_date - relativedelta(years=1)
    else:  # previous period
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=duration - 1)

    return prev_start, prev_end


def calculate_kpis(sales_df, start_date, end_date):
    """Calculate core KPIs for the dashboard."""
    # Normalize dates to date objects for comparison
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    elif isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).date()

    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date).date()

    # The date column in sales_df is already datetime.date objects
    mask = (sales_df['date'] >= start_date) & (sales_df['date'] <= end_date)

    filtered = sales_df[mask]

    # Exclude system accounts (show != 'Y')
    if 'show' in filtered.columns:
        filtered = filtered[filtered['show'] == 'Y']

    total_revenue = filtered['retail'].sum()
    total_quantity = filtered['quantity'].sum()
    total_gross = filtered['gross'].sum()
    active_customers = filtered['accno'].nunique()

    margin_pct = (total_gross / total_revenue * 100) if total_revenue != 0 else 0

    return {
        'revenue': total_revenue,
        'quantity': total_quantity,
        'gross_profit': total_gross,
        'margin_pct': margin_pct,
        'active_customers': active_customers
    }


def segment_customers(sales_df, accounts_df, as_of_date, lookback_days=90):
    """
    Segment customers into New, Repeat, At-Risk, and Dormant.

    Returns DataFrame with customer segments.
    """
    # Normalize as_of_date
    if hasattr(as_of_date, 'date'):
        as_of_date = as_of_date.date()
    elif isinstance(as_of_date, str):
        as_of_date = pd.to_datetime(as_of_date).date()

    # Filter to visible accounts only
    visible_accounts = accounts_df[accounts_df['show'] == 'Y']['accno'].unique()
    customer_sales = sales_df[sales_df['accno'].isin(visible_accounts)]

    # Get customer stats - date column contains datetime.date objects
    customer_stats = customer_sales.groupby('accno').agg({
        'date': ['min', 'max', 'count'],
        'retail': 'sum'
    }).reset_index()
    customer_stats.columns = ['accno', 'first_purchase', 'last_purchase', 'transaction_count', 'total_revenue']

    # The date column already contains datetime.date objects
    customer_stats['last_purchase_date'] = customer_stats['last_purchase']
    customer_stats['first_purchase_date'] = customer_stats['first_purchase']

    # Calculate days since last purchase
    customer_stats['days_since_last'] = customer_stats['last_purchase_date'].apply(
        lambda x: (as_of_date - x).days if x else 999
    )

    # Segment logic
    def get_segment(row):
        days_since = row['days_since_last']
        first_purchase = row['first_purchase_date']
        tx_count = row['transaction_count']

        # New: First purchase within 30 days
        if first_purchase and (as_of_date - first_purchase).days <= 30:
            return 'New'
        # Dormant: No purchase in 90+ days
        elif days_since > lookback_days:
            return 'Dormant'
        # At-Risk: Only 1 transaction and last purchase > 30 days ago
        elif tx_count == 1 and days_since > 30:
            return 'At-Risk'
        # Repeat: Multiple purchases, active within lookback
        else:
            return 'Repeat'

    customer_stats['segment'] = customer_stats.apply(get_segment, axis=1)

    return customer_stats


def get_category_breakdown(sales_df, start_date, end_date):
    """Get revenue and quantity breakdown by product category."""
    # Normalize dates
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    elif isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).date()

    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date).date()

    mask = (sales_df['date'] >= start_date) & (sales_df['date'] <= end_date)
    filtered = sales_df[mask]

    # Exclude system accounts
    if 'show' in filtered.columns:
        filtered = filtered[filtered['show'] == 'Y']

    # Group by category
    category_stats = filtered.groupby('category').agg({
        'retail': 'sum',
        'quantity': 'sum',
        'gross': 'sum'
    }).reset_index()

    category_stats['margin_pct'] = (category_stats['gross'] / category_stats['retail'] * 100).fillna(0)
    category_stats = category_stats.sort_values('retail', ascending=False)

    return category_stats


def get_top_customers(sales_df, accounts_df, start_date, end_date, n=10):
    """Get top N customers by revenue."""
    # Normalize dates
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    elif isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).date()

    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date).date()

    mask = (sales_df['date'] >= start_date) & (sales_df['date'] <= end_date)
    filtered = sales_df[mask]

    # Exclude system accounts
    if 'show' in filtered.columns:
        filtered = filtered[filtered['show'] == 'Y']

    # Group by customer
    customer_stats = filtered.groupby('accno').agg({
        'retail': 'sum',
        'quantity': 'sum',
        'gross': 'sum'
    }).reset_index()

    # Merge with account names
    customer_stats = customer_stats.merge(
        accounts_df[['accno', 'name']], on='accno', how='left'
    )

    customer_stats = customer_stats.sort_values('retail', ascending=False).head(n)

    return customer_stats


def get_top_products(sales_df, items_df, start_date, end_date, n=10):
    """Get top N products by revenue."""
    # Normalize dates
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    elif isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).date()

    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date).date()

    mask = (sales_df['date'] >= start_date) & (sales_df['date'] <= end_date)
    filtered = sales_df[mask]

    # Exclude system accounts
    if 'show' in filtered.columns:
        filtered = filtered[filtered['show'] == 'Y']

    # Group by product
    product_stats = filtered.groupby('item_number').agg({
        'retail': 'sum',
        'quantity': 'sum',
        'gross': 'sum'
    }).reset_index()

    # Merge with item descriptions
    product_stats = product_stats.merge(
        items_df[['item_number', 'description', 'category', 'image_file_path']],
        on='item_number', how='left'
    )

    product_stats = product_stats.sort_values('retail', ascending=False).head(n)

    return product_stats


def get_monthly_revenue(sales_df, start_date, end_date):
    """Get monthly revenue trend."""
    # Normalize dates
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    elif isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).date()

    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date).date()

    df = sales_df.copy()
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    filtered = df[mask]

    # Exclude system accounts
    if 'show' in filtered.columns:
        filtered = filtered[filtered['show'] == 'Y']

    # Convert date to datetime for period grouping
    filtered = filtered.copy()
    filtered['date_dt'] = pd.to_datetime(filtered['date'])

    # Group by month
    filtered['month'] = filtered['date_dt'].dt.to_period('M')
    monthly = filtered.groupby('month').agg({
        'retail': 'sum',
        'quantity': 'sum',
        'gross': 'sum'
    }).reset_index()

    monthly['month'] = monthly['month'].dt.to_timestamp()

    return monthly


def get_regional_breakdown(sales_df, accounts_df, start_date, end_date):
    """Get sales breakdown by region."""
    # Normalize dates
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    elif isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).date()

    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date).date()

    mask = (sales_df['date'] >= start_date) & (sales_df['date'] <= end_date)
    filtered = sales_df[mask]

    # Exclude system accounts
    if 'show' in filtered.columns:
        filtered = filtered[filtered['show'] == 'Y']

    # Merge with area codes from accounts
    if 'area' not in filtered.columns:
        filtered = filtered.merge(
            accounts_df[['accno', 'area']], on='accno', how='left'
        )

    # Map area codes to region names
    filtered['region'] = filtered['area'].apply(get_region_name)

    # Group by region
    regional = filtered.groupby('region').agg({
        'retail': 'sum',
        'quantity': 'sum',
        'accno': 'nunique'
    }).reset_index()

    regional.columns = ['region', 'revenue', 'quantity', 'customer_count']
    regional = regional.sort_values('revenue', ascending=False)

    return regional
