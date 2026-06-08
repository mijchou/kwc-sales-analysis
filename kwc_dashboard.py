"""
KWC Sales Dashboard powered by Claude
Main executive dashboard with simple, actionable metrics for the sales team.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import dashboard_utils as du


def display_kwc_dashboard(sales_data, accounts_df, items_df, max_date):
    """Main dashboard display function."""

    st.markdown("# KWC Sales Dashboard")
    st.caption("Powered by Claude")

    # Period selection
    st.markdown("### Select Period")
    period_cols = st.columns(6)

    # Initialize period state
    if 'dashboard_period' not in st.session_state:
        st.session_state.dashboard_period = 'this_month'

    with period_cols[0]:
        if st.button("This Month", type="primary" if st.session_state.dashboard_period == 'this_month' else "secondary", use_container_width=True):
            st.session_state.dashboard_period = 'this_month'
            st.rerun()
    with period_cols[1]:
        if st.button("Last Month", type="primary" if st.session_state.dashboard_period == 'last_month' else "secondary", use_container_width=True):
            st.session_state.dashboard_period = 'last_month'
            st.rerun()
    with period_cols[2]:
        if st.button("This Quarter", type="primary" if st.session_state.dashboard_period == 'this_quarter' else "secondary", use_container_width=True):
            st.session_state.dashboard_period = 'this_quarter'
            st.rerun()
    with period_cols[3]:
        if st.button("Last Quarter", type="primary" if st.session_state.dashboard_period == 'last_quarter' else "secondary", use_container_width=True):
            st.session_state.dashboard_period = 'last_quarter'
            st.rerun()
    with period_cols[4]:
        if st.button("This Year", type="primary" if st.session_state.dashboard_period == 'this_year' else "secondary", use_container_width=True):
            st.session_state.dashboard_period = 'this_year'
            st.rerun()
    with period_cols[5]:
        if st.button("All Time", type="primary" if st.session_state.dashboard_period == 'all_time' else "secondary", use_container_width=True):
            st.session_state.dashboard_period = 'all_time'
            st.rerun()

    # Calculate date range based on period selection
    start_date, end_date = get_period_dates(max_date, st.session_state.dashboard_period)
    prev_start, prev_end = du.get_comparison_period(start_date, end_date, 'previous')

    # Display date range info
    st.caption(f"Showing: {start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}")

    st.divider()

    # Calculate KPIs
    current_kpis = du.calculate_kpis(sales_data, start_date, end_date)
    previous_kpis = du.calculate_kpis(sales_data, prev_start, prev_end)

    # KPI Cards Row
    kpi_cols = st.columns(4)

    with kpi_cols[0]:
        delta_revenue = du.calculate_delta(current_kpis['revenue'], previous_kpis['revenue'])
        st.metric(
            label="Revenue",
            value=du.format_currency(current_kpis['revenue']),
            delta=f"{delta_revenue:+.1f}% vs prev period"
        )

    with kpi_cols[1]:
        delta_qty = du.calculate_delta(current_kpis['quantity'], previous_kpis['quantity'])
        st.metric(
            label="Units Sold",
            value=du.format_number(current_kpis['quantity']),
            delta=f"{delta_qty:+.1f}% vs prev period"
        )

    with kpi_cols[2]:
        delta_margin = current_kpis['margin_pct'] - previous_kpis['margin_pct']
        st.metric(
            label="Gross Profit",
            value=du.format_currency(current_kpis['gross_profit']),
            delta=f"{current_kpis['margin_pct']:.1f}% margin ({delta_margin:+.1f}pp)"
        )

    with kpi_cols[3]:
        delta_customers = current_kpis['active_customers'] - previous_kpis['active_customers']
        st.metric(
            label="Active Customers",
            value=current_kpis['active_customers'],
            delta=f"{delta_customers:+d} vs prev period"
        )

    st.divider()

    # Row 2: Revenue Trend and Category Breakdown
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.markdown("### Revenue Trend")
        display_revenue_trend(sales_data, start_date, end_date)

    with row2_col2:
        st.markdown("### Category Performance")
        display_category_breakdown(sales_data, start_date, end_date)

    st.divider()

    # Row 3: Top Customers and Customer Health
    row3_col1, row3_col2 = st.columns(2)

    with row3_col1:
        st.markdown("### Top 10 Customers")
        display_top_customers(sales_data, accounts_df, start_date, end_date)

    with row3_col2:
        st.markdown("### Customer Health")
        display_customer_health(sales_data, accounts_df, end_date)

    st.divider()

    # Row 4: Top Products and Regional Breakdown
    row4_col1, row4_col2 = st.columns(2)

    with row4_col1:
        st.markdown("### Top Products")
        display_top_products(sales_data, items_df, start_date, end_date)

    with row4_col2:
        st.markdown("### Regional Breakdown")
        display_regional_breakdown(sales_data, accounts_df, start_date, end_date)


def get_period_dates(max_date, period):
    """Calculate start and end dates based on period selection."""
    if isinstance(max_date, datetime):
        end_date = max_date
    else:
        end_date = datetime.combine(max_date, datetime.min.time())

    if period == 'this_month':
        start_date = end_date.replace(day=1)
    elif period == 'last_month':
        end_date = end_date.replace(day=1) - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif period == 'this_quarter':
        quarter = (end_date.month - 1) // 3
        start_date = end_date.replace(month=quarter * 3 + 1, day=1)
    elif period == 'last_quarter':
        quarter = (end_date.month - 1) // 3
        end_date = end_date.replace(month=quarter * 3 + 1, day=1) - timedelta(days=1)
        quarter = (end_date.month - 1) // 3
        start_date = end_date.replace(month=quarter * 3 + 1, day=1)
    elif period == 'this_year':
        start_date = end_date.replace(month=1, day=1)
    elif period == 'all_time':
        start_date = datetime(2020, 1, 1)
    else:
        start_date = end_date - timedelta(days=30)

    return start_date, end_date


def display_revenue_trend(sales_data, start_date, end_date):
    """Display monthly revenue trend chart."""
    monthly_data = du.get_monthly_revenue(sales_data, start_date, end_date)

    if monthly_data.empty:
        st.info("No data available for this period")
        return

    fig = px.line(
        monthly_data,
        x='month',
        y='retail',
        markers=True,
        labels={'month': 'Month', 'retail': 'Revenue (R)'}
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
        height=300,
        xaxis_title='',
        yaxis_title='Revenue (R)',
        hovermode='x unified'
    )

    fig.update_traces(
        line_color='#1f77b4',
        marker_size=8,
        hovertemplate='%{y:,.0f}<extra></extra>'
    )

    st.plotly_chart(fig, use_container_width=True)


def display_category_breakdown(sales_data, start_date, end_date):
    """Display category breakdown as pie chart."""
    category_data = du.get_category_breakdown(sales_data, start_date, end_date)

    if category_data.empty:
        st.info("No data available for this period")
        return

    # Filter out Others and unknown categories for cleaner chart
    main_categories = ['Crystal & Glass', 'Metal & Plastic', 'Metal Medals & Ribbons', 'Resin']
    filtered_data = category_data[category_data['category'].isin(main_categories)]

    if filtered_data.empty:
        filtered_data = category_data

    fig = px.pie(
        filtered_data,
        values='retail',
        names='category',
        color='category',
        color_discrete_map={
            'Crystal & Glass': '#636EFA',
            'Metal & Plastic': '#EF553B',
            'Metal Medals & Ribbons': '#00CC96',
            'Resin': '#AB63FA',
            'Others': '#FFA15A'
        }
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5),
        margin=dict(l=0, r=0, t=10, b=0),
        height=300
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>R %{value:,.0f}<br>%{percent}<extra></extra>'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Show margin comparison below
    st.caption("Margin by Category:")
    margin_cols = st.columns(len(filtered_data))
    for i, (_, row) in enumerate(filtered_data.iterrows()):
        with margin_cols[i]:
            cat_name = row['category'].split(' & ')[0][:10]  # Shorten name
            st.metric(cat_name, f"{row['margin_pct']:.0f}%", label_visibility='visible')


def display_top_customers(sales_data, accounts_df, start_date, end_date):
    """Display top customers bar chart."""
    top_customers = du.get_top_customers(sales_data, accounts_df, start_date, end_date, n=10)

    if top_customers.empty:
        st.info("No data available for this period")
        return

    # Truncate long names
    top_customers['display_name'] = top_customers['name'].str[:20]

    fig = px.bar(
        top_customers,
        x='retail',
        y='display_name',
        orientation='h',
        labels={'retail': 'Revenue (R)', 'display_name': ''},
        color='retail',
        color_continuous_scale='Blues'
    )

    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title='Revenue (R)'
    )

    fig.update_traces(
        hovertemplate='%{y}<br>R %{x:,.0f}<extra></extra>'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Link to legacy detail
    if st.button("View detailed customer analysis", key="link_customer_legacy"):
        st.session_state.current_page = "Sales Overview"
        st.rerun()


def display_customer_health(sales_data, accounts_df, as_of_date):
    """Display customer health donut chart."""
    customer_segments = du.segment_customers(sales_data, accounts_df, as_of_date)

    if customer_segments.empty:
        st.info("No customer data available")
        return

    # Count by segment
    segment_counts = customer_segments.groupby('segment').size().reset_index(name='count')

    # Define colors for segments
    color_map = {
        'New': '#00CC96',
        'Repeat': '#636EFA',
        'At-Risk': '#FFA15A',
        'Dormant': '#EF553B'
    }

    fig = go.Figure(data=[go.Pie(
        labels=segment_counts['segment'],
        values=segment_counts['count'],
        hole=0.5,
        marker_colors=[color_map.get(seg, '#999') for seg in segment_counts['segment']]
    )])

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5),
        margin=dict(l=0, r=0, t=10, b=0),
        height=280,
        annotations=[dict(text=f"{segment_counts['count'].sum()}<br>Total", x=0.5, y=0.5, font_size=16, showarrow=False)]
    )

    fig.update_traces(
        textposition='inside',
        textinfo='value',
        hovertemplate='%{label}<br>%{value} customers<br>%{percent}<extra></extra>'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Quick stats below
    stat_cols = st.columns(4)
    segment_order = ['New', 'Repeat', 'At-Risk', 'Dormant']
    for i, seg in enumerate(segment_order):
        count = segment_counts[segment_counts['segment'] == seg]['count'].values
        count = count[0] if len(count) > 0 else 0
        with stat_cols[i]:
            st.metric(seg, count)


def display_top_products(sales_data, items_df, start_date, end_date):
    """Display top products with images."""
    top_products = du.get_top_products(sales_data, items_df, start_date, end_date, n=5)

    if top_products.empty:
        st.info("No data available for this period")
        return

    for _, product in top_products.iterrows():
        col1, col2 = st.columns([1, 4])
        with col1:
            image_path = product.get('image_file_path', '')
            if pd.notna(image_path) and 'no_image' not in str(image_path):
                try:
                    st.image(image_path.replace('/app/', ''), width=60)
                except:
                    st.write("--")
            else:
                st.write("--")
        with col2:
            st.markdown(f"**{product['item_number']}**")
            desc = str(product.get('description', ''))[:40]
            st.caption(f"{desc} | {du.format_currency(product['retail'])} | {int(product['quantity'])} units")

    # Link to legacy detail
    if st.button("View detailed product analysis", key="link_product_legacy"):
        st.session_state.current_page = "Sales Overview"
        st.rerun()


def display_regional_breakdown(sales_data, accounts_df, start_date, end_date):
    """Display regional breakdown as horizontal bar chart."""
    regional_data = du.get_regional_breakdown(sales_data, accounts_df, start_date, end_date)

    if regional_data.empty:
        st.info("No regional data available")
        return

    # Filter out Unknown and small regions
    regional_data = regional_data[regional_data['region'] != 'Unknown']
    regional_data = regional_data.head(8)  # Top 8 regions

    fig = px.bar(
        regional_data,
        x='revenue',
        y='region',
        orientation='h',
        labels={'revenue': 'Revenue (R)', 'region': ''},
        color='revenue',
        color_continuous_scale='Greens'
    )

    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=10, b=0),
        height=300,
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title='Revenue (R)'
    )

    fig.update_traces(
        hovertemplate='%{y}<br>R %{x:,.0f}<extra></extra>'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary stats
    total_regions = len(regional_data)
    top_region = regional_data.iloc[0]['region'] if len(regional_data) > 0 else 'N/A'
    st.caption(f"Top region: **{top_region}** | {total_regions} regions with sales")
