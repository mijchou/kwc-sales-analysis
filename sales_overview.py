import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import utils as u

# test commit 
# Section 1: Item Ranking
# Function to display sales overview
def display_sales_overview(sales_data, accounts_df, purchase_record_df, items_df, date_start, date_end, supplier, selected_categories, metric_option):#, display_option):

    # Initiate values
    if metric_option == 'quantity':
        metric_option_name = 'Qty. Sold'
        metric_other = 'retail'
        metric_other_name = 'Revenue'

    elif metric_option == 'retail':
        metric_option_name = 'Revenue'
        metric_other = 'quantity'
        metric_other_name = 'Qty. Sold'

    # Align buttons to the right
    st.markdown(
    """
    <style>
        div[data-testid="column"]:nth-of-type(3)
        {
            text-align: end;
        } 
    </style>
    """,unsafe_allow_html=True
)

    ## Data Processing

    # Filter data based on selected date range
    filtered_data = sales_data[(sales_data['date'] >= date_start) & (sales_data['date'] <= date_end)]

    # Filter data based on selected suppliers
    if supplier:
        filtered_data = filtered_data[filtered_data['supplier'].isin(supplier)]

    # Filter data based on selected categories
    if selected_categories:
        filtered_data = filtered_data[filtered_data['category'].isin(selected_categories)]

    # If there are transaction records
    if not filtered_data.empty:
            
        # Calculate the quantity sold and total revenue per item number in the filtered date range
        sales_summary = filtered_data.groupby('item_number').agg({'quantity': 'sum', 'retail': 'sum'}).reset_index()
        # sales_summary = sales_summary.sort_values(by='retail', ascending=False).reset_index(drop=True)

        # Merge the sales summary with the items_df to get other info
        ranked_sales = pd.merge(sales_summary, items_df[['item_number', 'description', 'instock', 'image_file_path', 'retail']], on='item_number', how='left')
        ranked_sales.rename(columns={'retail_x': 'retail', 'retail_y': 'price'}, inplace=True)
        # # Update the session state with the new ranked_sales dataframe
        # st.session_state.df = ranked_sales[['item_number', 'description', 'retail', 'quantity']]

        # Calculate customer ranking
        customer_ranking = filtered_data.groupby(['accno', 'name', 'termcode', 'delimit']).agg({'retail': 'sum', 'quantity': 'sum'}).reset_index()

        # Calculate for accno daily transaction: filtered_data by accno, date > total quantity, total retail
        # customer_purchase_by_date = filtered_data.groupby(['accno', 'date']).agg({'quantity': 'sum', 'retail': 'sum'}).reset_index()
        # sales_summary = sales_summary.sort_values(by='retail', ascending=False).reset_index(drop=True)

        # Calculate customer purchase by date
        sales_over_time_by_customer = filtered_data.groupby(['accno','date']).agg({'retail': 'sum', 'quantity': 'sum'}).reset_index()


        # Calculate: filtered_data by accno, date > total quantity, total retail
        customer_purchase_by_item = filtered_data.groupby(['accno', 'item_number']).agg({'quantity': 'sum', 'retail': 'sum'}).reset_index()

        # Calculate total revenue over time
        # revenue_over_time = filtered_data.groupby('date').agg({'quantity': 'sum', 'retail': 'sum'}).reset_index()
        # revenue_over_time['date'] = pd.to_datetime(revenue_over_time['date']).dt.strftime('%Y-%m-%d')
        # revenue_over_time = revenue_over_time.sort_values(by='date', ascending=True).reset_index(drop=True)

        # Calculate metrics
        # total_revenue = filtered_data['retail'].sum()
        # total_quantity_sold = filtered_data['quantity'].sum()


        ## Display metrics: Revenue and Quantity
        # container = st.container(border=True)
        # with container:
        #     col1, col2 = st.columns(2)
        #     col1.metric("Total Revenue (Total Excl.)", f"R {total_revenue:,.2f}")
        #     col2.metric("Total Quantity Sold", f"{total_quantity_sold:,.0f}")



        # Page starts
        st.header("Sales Overview", divider='grey')

        # Section 1: Item Sales Ranking
        col1, col2 = st.columns([5.5, 4.5])

        ## Item Sales Rank title, table
        with col1:
            st.subheader('Items Sales Rank')#, divider='grey')
            st.markdown('&nbsp;&nbsp;&nbsp;:arrow_down: :blue[**Click to select an item.**]')
            ranked_sales = ranked_sales[['image_file_path', 'item_number', 'description', 'retail', 'quantity', 'instock']].sort_values(by=metric_option, ascending=False).reset_index(drop=True)
            selected_item_row = st.dataframe(ranked_sales,
                                        column_config={"image_file_path": st.column_config.ImageColumn("Image"),
                                        "item_number": st.column_config.Column("Item Number"),
                                        "description": st.column_config.Column("Description"),
                                        "retail": st.column_config.Column("Revenue"),
                                        "quantity": st.column_config.Column("Qty. Sold"),
                                        "instock": st.column_config.Column("In Stock")},
                                        # "price": st.column_config.Column("Price")},
                                        hide_index=True, on_select="rerun", selection_mode="single-row", height=700, key='item_rank_table')
        
        ## Item Sales Rank preview
        with col2:
            selected_rowno = selected_item_row.selection.rows
            # item_number_colno = ranked_sales.columns.get_loc('item_number')
            selected_df = ranked_sales.iloc[selected_rowno, 1]
            if not selected_df.empty:
                item_number = selected_df.iloc[0]
                header = item_number
            else:
                item_number = ranked_sales['item_number'][0]
                header = f':trophy: Top-selling: {item_number}'
            item_description = items_df.loc[items_df['item_number'] == item_number, 'description'].iloc[0]

            # display info
            st.subheader(header)
            st.markdown(f':grey[{item_description}]')
            image_path = items_df.loc[items_df['item_number'] == item_number, 'image_file_path'].iloc[0]
            st.image(image_path)
            st.subheader('Stock Count History Preview')
            u.plot_stock_history(sales_data,
                    purchase_record_df,
                    accounts_df,
                    item_number, items_df, date_start, date_end, xrange=None, yrange=None, height=250, show_accno=False)#, title=f'Stock Count History Preview')
        
            # Button to link to Sales Analysis
            col1, col2, col3 = st.columns(3)
            with col3:
                if st.button("See Details"):
                    st.session_state.previous_page = st.session_state.current_page
                    st.session_state.current_page = "Sales Analysis"
                    st.session_state.selected_item_number = item_number
                    st.experimental_rerun()

        st.divider()





        # Section 2: Customer Purchase Ranking

        # create df to display
        customer_ranking = customer_ranking[['accno', 'name', 'termcode', 'delimit', 'retail', 'quantity']].sort_values(by=metric_option, ascending=False).reset_index(drop=True)

        col1, col2 = st.columns([5, 5])
        ## Show customer Rank table
        with col1:
            st.subheader('Customer Purchase Ranking') #, divider='grey')
            st.markdown('&nbsp;&nbsp;&nbsp;:arrow_down: :blue[**Click to select an item.**]')
            selected_customer_row = st.dataframe(customer_ranking,
                                        column_config={"accno": st.column_config.Column("Account"),
                                        "name": st.column_config.Column("Name"),
                                        "termcode": st.column_config.Column("Acc. Type"),
                                        "delimit": st.column_config.Column("Acc. Limit"),
                                        "retail": st.column_config.Column("Revenue"),
                                        "quantity": st.column_config.Column("Qty. Sold")},
                                        hide_index=True, on_select="rerun", selection_mode="single-row", height=600)
            selected_rowno = selected_customer_row.selection.rows # row number
            # accno_colno = customer_ranking.columns.get_loc('accno') # column number
            selected_df = customer_ranking.iloc[selected_rowno, 0]
            if not selected_df.empty:
                selected_customer_number = selected_df.iloc[0]
                selected_customer_name = accounts_df[accounts_df['accno']==selected_customer_number]['name'].values[0]
                col2.subheader(f'{selected_customer_name} :blue[({selected_customer_number})]')
            else:
                selected_customer_number = customer_ranking['accno'][0]
                selected_customer_name = accounts_df[accounts_df['accno']==selected_customer_number]['name'].values[0]
                col2.subheader(f':trophy: Top Customer: {selected_customer_name} :blue[({selected_customer_number})]')

        ## Show customer Rank Preview
        with col2:
            st.subheader("Top Purchased Items")
            # customer_item_df = customer_purchase_by_item[customer_purchase_by_item['accno'] == selected_customer_number][['item_number', 'quantity', 'retail']].sort_values(by=metric_option, ascending=False).reset_index(drop=True)
            customer_item_list = customer_purchase_by_item[customer_purchase_by_item['accno'] == selected_customer_number].sort_values(by=metric_option, ascending=False)['item_number'].head(40).tolist()
            # Filter the DataFrame for the specific item numbers
            customer_items_df = items_df.loc[items_df['item_number'].isin(customer_item_list)]
            # Retrieve the image file paths
            top_items_image_paths = customer_items_df['image_file_path'].unique()[:10].tolist()
            # customer_item_df = pd.merge(customer_item_df, items_df[['item_number', 'image_file_path']], on='item_number', how='left')
            # customer_item_list = customer_item_df['image_file_path'].unique()

            # Determine the number of items to display (up to 6)
            num_items_to_display = min(10, len(top_items_image_paths))

            # Create columns dynamically based on the number of items to display
            cols = st.columns(5) + st.columns(5)

            # Display the images in the respective columns
            for i in range(num_items_to_display):
                with cols[i]:
                    st.image(top_items_image_paths[i])

            # Sales Over Time Graph
            st.subheader("Sales Over Time Preview")
            sales_over_time_by_customer = sales_over_time_by_customer[sales_over_time_by_customer['accno']==selected_customer_number]
            sales_over_time_by_customer['date_str'] = pd.to_datetime(sales_over_time_by_customer['date']).dt.strftime('%Y-%m-%d')
            ## set hoverplate
            if metric_option=='quantity':
                hovertemplate2 = '<b>Date: </b>%{customdata[0]}<br><b>Qty. Sold: </b>%{y}<br><b>Revenue: </b>R %{customdata[1]}<extra></extra>'
            elif metric_option=='retail':
                hovertemplate2 = '<b>Date: </b>%{customdata[0]}<br><b>Revenue: </b>%{y}<br><b>Qty. Sold: </b>%{customdata[1]}<extra></extra>'
            fig_sales_over_time = px.line(sales_over_time_by_customer, x='date', y=metric_option)#, hover_data={metric_other: True})
            fig_sales_over_time.update_traces(hovertemplate=hovertemplate2,
                                                customdata=sales_over_time_by_customer[['date_str', metric_other]].values,
                                                mode="markers+lines")
            fig_sales_over_time.update_layout(xaxis_title='Date', yaxis_title=metric_option_name, margin=dict(t=0, b=0), height=300, 
                                                hoverlabel=dict(bgcolor="white", font_color='black', font_size=14),
                                                hovermode="x")
            fig_sales_over_time.update_xaxes(tickformat='%b %d')
            st.plotly_chart(fig_sales_over_time)




            col1, col2, col3 = st.columns(3)
            with col3:
                if st.button("See Details", key='customer_analysis_details'):
                    st.session_state.previous_page = st.session_state.current_page
                    st.session_state.current_page = "Customer Analysis"
                    st.session_state.selected_customer_number = selected_customer_number
                    st.experimental_rerun()

    else:
        st.write("No transaction records found.")

    # Scroll to top of page every visit
    u.scroll_to_top()