import streamlit as st
import pandas as pd
import utils as u
import dashboard_utils as du


# 進貨分析表 (Stock-in Analysis)
# Shows the Items Sales Rank table plus recency columns (last sale date/customer/qty
# and last stock-in date) to spot items that have recently sold out and who last
# bought them. Sales metrics (Revenue/Qty/毛利) follow the sidebar date filter, while
# the last-sale and last-stock-in dates are always all-time.
def display_stock_in_analysis(sales_data, accounts_df, purchase_record_df, items_df, date_start, date_end, supplier, selected_categories, metric_option, cost_price_df=None):

    ## Data Processing

    # Filter data based on selected date range
    filtered_data = sales_data[(sales_data['date'] >= date_start) & (sales_data['date'] <= date_end)]

    # Filter data based on selected suppliers
    if supplier:
        filtered_data = filtered_data[filtered_data['supplier'].isin(supplier)]

    # Filter data based on selected categories
    if selected_categories:
        filtered_data = filtered_data[filtered_data['category'].isin(selected_categories)]

    st.header("進貨分析表", divider='grey')

    # If there are transaction records
    if not filtered_data.empty:

        # Calculate the quantity sold and total revenue per item in the filtered date range
        sales_summary = filtered_data.groupby('item_number').agg({'quantity': 'sum', 'retail': 'sum'}).reset_index()

        # Merge the sales summary with the items_df to get other info
        analysis_df = pd.merge(sales_summary, items_df[['item_number', 'description', 'instock', 'image_file_path']], on='item_number', how='left')

        # Always add 毛利 (profit margin) on this page
        if cost_price_df is not None:
            analysis_df = du.add_profit_margin(analysis_df, cost_price_df)
        else:
            analysis_df['毛利'] = 0

        # Last real sale per item (all-time): exclude returns (quantity > 0) and
        # internal/system accounts (show == 'Y'); take the most recent transaction.
        real_sales = sales_data[(sales_data['quantity'] > 0) & (sales_data['show'] == 'Y')]
        last_sale = (real_sales.sort_values('date')
                        .groupby('item_number')
                        .tail(1)[['item_number', 'date', 'accno', 'name', 'quantity']]
                        .rename(columns={'date': 'last_sale_date', 'accno': 'last_sale_accno',
                                         'name': 'last_sale_customer', 'quantity': 'last_sale_qty'}))

        # Last stock-in date per item (all-time)
        last_stockin = (purchase_record_df.groupby('item_number')['date'].max()
                            .reset_index().rename(columns={'date': 'last_stockin_date'}))

        # Assemble the analysis table
        analysis_df = analysis_df.merge(last_sale, on='item_number', how='left')
        analysis_df = analysis_df.merge(last_stockin, on='item_number', how='left')
        analysis_df = analysis_df.sort_values(by=metric_option, ascending=False).reset_index(drop=True)

        st.markdown('&nbsp;&nbsp;&nbsp;:arrow_down: :blue[**Click to select a row, then use the buttons above.**]')

        # Display columns (exclude last_sale_accno, kept only for navigation)
        display_cols = ['image_file_path', 'item_number', 'description', 'retail', 'quantity',
                        '毛利', 'instock', 'last_sale_date', 'last_sale_customer', 'last_sale_qty',
                        'last_stockin_date']
        display_df = analysis_df[display_cols]
        column_config = {
            "image_file_path": st.column_config.ImageColumn("Image"),
            "item_number": st.column_config.Column("Item Number"),
            "description": st.column_config.Column("Description"),
            "retail": st.column_config.Column("Revenue"),
            "quantity": st.column_config.Column("Qty. Sold"),
            "毛利": st.column_config.NumberColumn("毛利", format="%.2f"),
            "instock": st.column_config.Column("In Stock"),
            "last_sale_date": st.column_config.DateColumn("Last Sale Date", format="YYYY-MM-DD"),
            "last_sale_customer": st.column_config.Column("Last Sale Customer"),
            "last_sale_qty": st.column_config.Column("Last Sale Qty"),
            "last_stockin_date": st.column_config.DateColumn("Last Stock-in Date", format="YYYY-MM-DD"),
        }

        # Reserve space for the buttons above the table, then render the table so we
        # can fill the buttons with the current selection.
        button_area = st.container()
        selected_row = st.dataframe(display_df,
                                    column_config=column_config,
                                    hide_index=True, on_select="rerun", selection_mode="single-row",
                                    height=700, key='stock_in_table')

        rows = selected_row.selection.rows
        has_sel = len(rows) > 0
        sel_item = analysis_df.iloc[rows[0]]['item_number'] if has_sel else None
        sel_accno = analysis_df.iloc[rows[0]]['last_sale_accno'] if has_sel else None

        with button_area:
            c1, c2, _ = st.columns([2, 2, 6])
            with c1:
                if st.button("🔗 Link to item", disabled=not has_sel, key='stock_in_link_item'):
                    st.session_state.previous_page = st.session_state.current_page
                    st.session_state.current_page = "Sales Analysis"
                    st.session_state.selected_item_number = sel_item
                    st.rerun()
            with c2:
                if st.button("🔗 Link to customer", disabled=not (has_sel and pd.notna(sel_accno)), key='stock_in_link_customer'):
                    st.session_state.previous_page = st.session_state.current_page
                    st.session_state.current_page = "Customer Analysis"
                    st.session_state.selected_customer_number = sel_accno
                    st.rerun()

    else:
        st.write("No transaction records found.")

    # Scroll to top of page every visit
    u.scroll_to_top()
