import streamlit as st
import pandas as pd
import plotly.express as px
import utils as u
import datetime as dt
import numpy as np
from streamlit_plotly_events import plotly_events

def display_sales_analysis(sales_data, accounts_df, purchase_record_df, items_df, item_number, date_start, date_end, metric_option): #, display_option):

    if st.button("← Previous Page", key='sales_analysis_back_button_1'):
        u.go_back()

    # Initiate values
    if metric_option == 'quantity':
        metric_option_name = 'Qty. Sold'
        metric_other = 'retail'
        metric_other_name = 'Revenue'

    elif metric_option == 'retail':
        metric_option_name = 'Revenue'
        metric_other = 'quantity'
        metric_other_name = 'Qty. Sold'

    # Define functions

    ## refresh filtered data
    def refresh_filtered_data():
        filtered_data = sales_data[(sales_data['date'] >= date_start) & (sales_data['date'] <= date_end) & (sales_data['item_number'] == item_number)]
        
        # # Get Customer Ranking Dataframe
        # customer_ranking = filtered_data.groupby(['accno', 'name']).agg({metric_option: 'sum',  metric_other: 'sum'}).reset_index()
        # customer_ranking = customer_ranking.sort_values(by=metric_option, ascending=False).reset_index(drop=True)

        # # Number of Customer
        # no_of_customer = customer_ranking['accno'].nunique()
        
        return filtered_data #, customer_ranking, no_of_customer

    ## refresh metrics
    def refresh_metrics():
        total_quantity_sold = filtered_data['quantity'].sum() # Total Quantity        
        total_revenue = filtered_data['retail'].sum() # Total Revenue        
        # top_customer_number = filtered_data.groupby('accno')['quantity'].sum().idxmax() # Top Customer Number
        # top_customer_name = accounts_df[accounts_df['accno'] == top_customer_number]['name'].iloc[0] # Top Customer Name
        # total_customers = filtered_data['accno'].nunique() # Total Customer Number
        total_purchases = filtered_data.shape[0] # Total Purchase Number
        return total_quantity_sold, total_revenue, total_purchases

    # Create a secondary DataFrame for searches
    items_df2 = items_df.copy()

    # Set index for efficient lookup
    items_df2.set_index('item_number', inplace=True)


    ## refresh other data
    def refresh_info():
        # Get Item Description
        # item_description = items_df[items_df['item_number'] == item_number]['description'].iloc[0]
        item_description = items_df2.loc[item_number, 'description']

        # Get Category
        # category_row = items_df[items_df['item_number'] == item_number]
        # category = category_row['category'].values[0] if 'category' in category_row.columns else 'Unknown'
        category = items_df2.loc[item_number, 'category']

        # Get Image Path
        # image_path = u.find_image_path(item_number)

        # Get Current Retail Price
        # retail_price_row = items_df[items_df['item_number'] == item_number]
        # retail_price = retail_price_row['retail'].values[0] if not retail_price_row.empty else 'Unknown'
        retail_price = items_df2.loc[item_number, 'retail']

        # Get Current Instock Number
        # instock_row = items_df[items_df['item_number'] == item_number]
        # instock_quantity = int(instock_row['instock'].values[0]) if not instock_row.empty else 'Unknown'
        instock_quantity = items_df2.loc[item_number, 'instock']

        # Get Customer Ranking Dataframe
        customer_ranking = filtered_data.groupby(['accno', 'name']).agg({metric_option: 'sum',  metric_other: 'sum'}).reset_index()
        customer_ranking = customer_ranking.sort_values(by=metric_option, ascending=False).reset_index(drop=True)

        # Number of Customer
        no_of_customer = customer_ranking['accno'].nunique()

        return item_description, category, retail_price, instock_quantity, customer_ranking, no_of_customer



    # Load Data

    ## Load filtered data
    filtered_data = refresh_filtered_data()
    if not filtered_data.empty:
        ## Load metrics
        total_quantity_sold, total_revenue, total_purchases = refresh_metrics()
    else:
        total_quantity_sold = 0
        total_revenue = 0
    ## Load other data
    item_description, category, retail_price, instock_quantity, customer_ranking, no_of_customer = refresh_info()

    # Page Begin

    ## Section 1: Title, Image, same Series Items
    col1, col2 = st.columns(2)

    ## get image_path, same_series_df,
    # image_path = items_df[items_df['item_number']==item_number]['image_file_path'].values[0]
    image_path = items_df2.loc[item_number, 'image_file_path']
    
    # build same series df
    sales_data_by_date = sales_data[(sales_data['date'] >= date_start) & (sales_data['date'] <= date_end)] # filter sales by ranged dates
    same_series_df = items_df[items_df['image_file_path']==image_path][['item_number', 'description', 'instock', 'retail']].reset_index(drop=True) # get same series items

    # needed list of item_numbers
    same_series_item_numbers = same_series_df['item_number'].tolist()

    # Filter the DataFrame by the list of item_numbers
    same_series_sales = sales_data_by_date[sales_data_by_date['item_number'].isin(same_series_item_numbers)]

    # Group by item_number and sum the quantities
    quantity_sold = same_series_sales.groupby('item_number')['quantity'].sum().reset_index()

    # Get the final table
    same_series_df = pd.merge(same_series_df, quantity_sold[['item_number', 'quantity']], on='item_number', how='left') 


    with col2:
        st.header('Same Series Items')
        st.markdown('&nbsp;&nbsp;&nbsp;:arrow_down: :blue[**Click to check out another item.**]')
        # destined_item = item_number
        # def highlight_original_item(row):
        #     return ['background-color: lightyellow' if row['item_number']==item_number else '' for _ in row]
        # styled_df2 = same_series_df.style.apply(highlight_original_item, axis=1)
        ## clickable df: same_series_df
        selected_item_row = st.dataframe(same_series_df,
                                        column_config={"item_number": st.column_config.Column("Item Number"),
                                                       "description": st.column_config.Column("Description"),
                                                       "retail": st.column_config.Column("Price"),
                                                       "instock": st.column_config.Column("In Stock"),
                                                       "quantity": st.column_config.Column("Qty. Sold")
                                                       }, hide_index=True, on_select='rerun', selection_mode="single-row")

        ## link to another item from the same series
        selected_rowno = selected_item_row.selection.rows # get row no.
        selected_df = same_series_df.iloc[selected_rowno, 0] # get cell

        ## if any row selected, get the item_number; and update all other info
        if not selected_df.empty:
            item_number = selected_df.iloc[0]
            st.session_state.selected_item_number = item_number
            ## Update Item info
            filtered_data = refresh_filtered_data()
            item_description, category, retail_price, instock_quantity, customer_ranking, no_of_customer = refresh_info()
            if not filtered_data.empty:
                total_quantity_sold, total_revenue, total_purchases = refresh_metrics()
            else:
                total_quantity_sold = 0
                total_revenue = 0

    ## Show title, image
    with col1:
        col1, col2 = st.columns(2, vertical_alignment='bottom')
        col1.header(f':blue[{item_number}]')
        col2.header(f'Price: R {retail_price}')
        st.image(image_path, caption=item_description, use_column_width=True)

    st.divider()

    # Section 3: Stock History

    col1, col2 = st.columns([6.5, 3.5])
    ## plot stock history
    with col1:
        st.subheader('Stock History')
        stock_changes = u.plot_stock_history(sales_data, purchase_record_df, accounts_df, item_number, items_df, date_start, date_end, height=450)
    ## display table
    with col2:
        # metrics
        # container = st.container(border=True)
        # with container:
        col1, col2 = st.columns(2)
        col1.metric('In Stock', instock_quantity)
        col2.metric('Quantity Sold', total_quantity_sold)
        # rename columns
        stock_changes = stock_changes[['date', 'accno', 'name', 'stock_inout']].sort_values(by='date', ascending=False)
        # styling the dataframe
        def highlight_positive_quantity(row):
            return ['background-color: lightyellow' if row['accno']=='STOCK-IN' else '' for _ in row]
        styled_df = stock_changes.style.apply(highlight_positive_quantity, axis=1)
        st.dataframe(styled_df, column_config={"date": st.column_config.Column("Date"),
                                                "accno": st.column_config.Column("Account"),
                                                "name": st.column_config.Column("Name"),
                                                "stock_inout": st.column_config.Column("In/Out")
                                                }, hide_index=True, use_container_width=True)
    st.divider()


    # Section 4: Customer Purchase Rank
    if filtered_data.empty:
        st.markdown(f'No transaction records found from **{date_start}** to **{date_end}**.')
    else:
        col1, col2 = st.columns([6.5, 3.5])
        with col1:
            st.subheader('Customer Purchase Rank')
            if metric_option=='quantity':
                hovertemplate = '<b>%{x}</b><br><b>%{customdata[0]}</b><br>Qty. Sold: %{y}<br>Revenue: R %{customdata[1]}<extra></extra>'
            elif metric_option=='retail':
                hovertemplate = '<b>%{x}</b><br><b>%{customdata[0]}</b><br>Revenue: R %{y}<br>Qty. Sold: %{customdata[1]}<extra></extra>'
            fig3 = px.bar(customer_ranking, x='accno', y=metric_option,
                        hover_data={'name': True, metric_other: True})
            fig3.update_traces(hovertemplate=hovertemplate,
                            marker_color='#EFF2F6', 
                            marker_line_color='black', 
                            marker_line_width=2)
            fig3.update_layout(xaxis_title='Customer Number', yaxis_title=metric_option_name, bargap=0.2, hoverlabel=dict(bgcolor="white", font_color= 'black', font_size=14))
            fig3.update_xaxes(range=[-0.5, no_of_customer-0.5])
            st.plotly_chart(fig3, use_container_width=True)

            with col2:
                # customer_ranking = customer_ranking[['accno', 'name', 'quantity', 'retail']].sort_values(by=metric_option, ascending=False).reset_index(drop=True)
                top_customer_number = customer_ranking['accno'].iloc[0]
                total_customers = customer_ranking.shape[0]
                if not filtered_data.empty:
                    cola, colb = st.columns(2)
                    cola.metric('Top Customer', f'{top_customer_number}')
                    colb.metric('Total Customer Count', total_customers)
                st.markdown('&nbsp;&nbsp;&nbsp;:arrow_down: :blue[**Click to select a customer.**]')
                selected_customer_row = st.dataframe(customer_ranking,
                                                    column_config={"accno": st.column_config.Column("Account"),
                                                                    "name": st.column_config.Column("Name"),
                                                                    "retail": st.column_config.Column("Revenue"),
                                                                    "quantity": st.column_config.Column("Qty. Sold")},
                                                    use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", )

                selected_rowno = selected_customer_row.selection.rows
                selected_df = customer_ranking.iloc[selected_rowno, 0]
                if not selected_df.empty:
                    selected_customer_number = selected_df.iloc[0]
                else:
                    selected_customer_number = customer_ranking['accno'][0]

                if st.button("Link to Customer"):
                    st.session_state.previous_page = st.session_state.current_page
                    st.session_state.current_page = "Customer Analysis"
                    st.session_state.selected_customer_number = selected_customer_number
                    st.experimental_rerun()



        # if st.button("← Back to Sales Overview", key="sa_back_to_sales_overview"):
        #     u.back_to_sales_overview()

    if st.button("← Previous Page", key='sales_analysis_back_button_2'):
        u.go_back()





