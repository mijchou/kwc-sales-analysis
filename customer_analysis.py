import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import pandas as pd
import utils as u

# Function to display customer analysis
def display_customer_analysis(sales_data, accounts_df, customer_number, items_df, date_start, date_end, supplier, selected_categories, metric_option):

    # Initiate values
    if metric_option == 'quantity':
        metric_option_name = 'Qty. Sold'
        metric_other = 'retail'
        metric_other_name = 'Revenue'

    elif metric_option == 'retail':
        metric_option_name = 'Revenue'
        metric_other = 'quantity'
        metric_other_name = 'Qty. Sold'


    # Create a secondary DataFrame for searches
    accounts_df2 = accounts_df.copy()

    # Set index for efficient lookup
    accounts_df2.set_index('accno', inplace=True)


    if st.button("← Previous Page", key='customer_analysis_back_button_1'):
        u.go_back()

    # Filter data based on selected date range
    filtered_data = sales_data[(sales_data['accno'] == customer_number) & (sales_data['date'] >= date_start) & (sales_data['date'] <= date_end)]
    filtered_data['date'] = pd.to_datetime(filtered_data['date']).dt.date
    
    
    # Filter data based on selected suppliers
    if supplier:
        filtered_data = filtered_data[filtered_data['supplier'].isin(supplier)]
    
    # Filter data based on selected category
    if selected_categories:
        filtered_data = filtered_data[filtered_data['category'].isin(selected_categories)]

    # Get info from items_df
    filtered_data = pd.merge(filtered_data, items_df[['item_number', 'image_file_path']], on='item_number', how='left')

    # Create Address column
    # accounts_df['address'] = accounts_df['addr1'] + accounts_df['addr2'] + accounts_df['addr3']

    # Get info from accounts_df
    # customer_name = accounts_df[accounts_df['accno'] == customer_number]['name'].values[0]
    customer_name = accounts_df2.loc[customer_number, 'name']

    # customer_main_contact = accounts_df[accounts_df['accno'] == customer_number]['contact'].values[0]
    # customer_address = accounts_df[accounts_df['accno'] == customer_number]['address'].values[0]
    # customer_telephone = accounts_df[accounts_df['accno'] == customer_number]['tel'].values[0]
    # customer_email = accounts_df[accounts_df['accno'] == customer_number]['email'].values[0]

    # customer_acc_type = accounts_df[accounts_df['accno'] == customer_number]['termcode'].values[0]
    customer_acc_type = accounts_df2.loc[customer_number, 'termcode']
    # customer_acc_limit = accounts_df[accounts_df['accno'] == customer_number]['delimit'].values[0]
    customer_acc_limit = accounts_df2.loc[customer_number, 'delimit']
    # customer_disc_rate = accounts_df[accounts_df['accno'] == customer_number]['disc'].values[0]
    customer_disc_rate = accounts_df2.loc[customer_number, 'disc']

    # Title and basic info
    st.header(f"{customer_name} :blue[({customer_number})]", divider='grey')
    col1, col2, col3 = st.columns(3)
    col1.info(f'**Account Type:** {customer_acc_type}')#, icon="💁‍♀️")
    col2.info(f'**Account Limit:** R {customer_acc_limit}')#, icon="☎️")
    col3.info(f'**Discount Rate:** {int(customer_disc_rate)}%')#, icon="✉️")

    # If there are transaction records
    if not filtered_data.empty:







        # Section 1: Item Sales Ranking
        col1, col2 = st.columns([5, 5])
        col1.write("### Purchase Ranking")
        col2.markdown('&nbsp;&nbsp;&nbsp;:arrow_down: :blue[**Click to select an item.**]')
        top_selling_data = filtered_data.groupby(['item_number', 'description', 'image_file_path']).agg({'retail': 'sum', 'quantity': 'sum'}).reset_index()
        top_selling_data = top_selling_data[['image_file_path', 'item_number', 'description', 'retail', 'quantity']].sort_values(by=metric_option, ascending=False).reset_index(drop=True)
        
        with col1:
            # top_selling_data = top_selling_data.sort_values(by=metric_option, ascending=False)
            fig_top_selling_data = px.bar(top_selling_data, x='item_number', y=metric_option, hover_data={'description': True, metric_other: True})
            if metric_option=='quantity':
                hovertemplate1 = '<b>%{x}</b><br><b>%{customdata[0]}</b><br>Qty. Sold: %{y}<br>Revenue: R %{customdata[1]}<extra></extra>'
            elif metric_option=='retail':
                hovertemplate1 = '<b>%{x}</b><br><b>%{customdata[0]}</b><br>Revenue: R %{y}<br>Qty. Sold: %{customdata[1]}<extra></extra>'
            fig_top_selling_data.update_traces(hovertemplate=hovertemplate1,
                                                marker_color='#EFF2F6', 
                                                marker_line_color='black',
                                                marker_line_width=2)
            fig_top_selling_data.update_layout(xaxis_title='Item Number', yaxis_title=metric_option_name, bargap=0.2, hoverlabel=dict(bgcolor="white", font_color='black', font_size=14))
            fig_top_selling_data.update_xaxes(range=[-0.5, 8.5])
            # plotly_events(fig_top_selling_data, click_event=True)
            st.plotly_chart(fig_top_selling_data)

        with col2:
            selected_item_row = st.dataframe(top_selling_data, column_config={"image_file_path": st.column_config.ImageColumn("Image"),
                                        "item_number": st.column_config.Column("Item Number"),
                                        "description": st.column_config.Column("Description"),
                                        "quantity": st.column_config.Column("Qty. Sold"),
                                        "retail": st.column_config.Column("Revenue")},
                                            use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", )

            selected_rowno = selected_item_row.selection.rows
            selected_df = top_selling_data.iloc[selected_rowno, 1]
            if not selected_df.empty:
                item_number = selected_df.iloc[0]
            else:
                item_number = top_selling_data['item_number'][0]

            if st.button("Link to Item"):
                st.session_state.previous_page = st.session_state.current_page
                st.session_state.current_page = "Sales Analysis"
                st.session_state.selected_item_number = item_number
                st.experimental_rerun()







        st.divider()




        # Section 2: Sales Over Time
        col1, col2 = st.columns([6, 4])
        col1.subheader('Sales Over Time')

        # Calculate sales over time
        sales_over_time = filtered_data.groupby('date').agg({'retail': 'sum', 'quantity': 'sum'}).reset_index()
        sales_over_time['date_str'] = pd.to_datetime(sales_over_time['date']).dt.strftime('%Y-%m-%d')
        with col1:
                fig_sales_over_time = px.line(sales_over_time, x='date', y=metric_option, hover_data={metric_other: True})
                if metric_option=='quantity':
                    hovertemplate2 = '<b>Date: </b>%{customdata[0]}<br><b>Qty. Sold: </b>%{y}<br><b>Revenue: </b>R %{customdata[1]}<extra></extra>'
                elif metric_option=='retail':
                    hovertemplate2 = '<b>Date: </b>%{customdata[0]}<br><b>Revenue: </b>%{y}<br><b>Qty. Sold: </b>%{customdata[1]}<extra></extra>'
                fig_sales_over_time.update_traces(hovertemplate=hovertemplate2,
                                                    customdata=sales_over_time[['date_str', metric_other]].values,
                                                    mode="markers+lines")
                fig_sales_over_time.update_layout(xaxis_title='Date', yaxis_title=metric_option_name, bargap=0.2,
                                                    hoverlabel=dict(bgcolor="white", font_color='black', font_size=14),
                                                    hovermode="x")
                fig_sales_over_time.update_xaxes(tickformat='%b %d')                                            
                st.plotly_chart(fig_sales_over_time)


        with col2:
            # Revenue Analysis
            col1, col2 = st.columns(2)
            total_revenue = filtered_data['retail'].sum()
            total_quantity = filtered_data['quantity'].sum()
            col1.metric("Total Revenue (Total Excl.)", f"R {total_revenue:,.2f}")
            col2.metric("Total Quantity", f"{total_quantity:,.0f}")

            # Sales Over Time Records
            st.markdown('&nbsp;&nbsp;&nbsp;:arrow_down: :blue[**Click to view transactions.**]')
            selected_row = st.dataframe(sales_over_time[['date', 'retail', 'quantity']].sort_values(by='date', ascending=False),
                                        column_config={"date": st.column_config.Column("Date"),
                                                        "retail": st.column_config.Column("Revenue"),
                                                        "quantity": st.column_config.Column("Qty. Sold")}, hide_index=True, use_container_width=True, height=350, on_select='rerun', selection_mode="single-row")
            selected_rowno = selected_row.selection.rows # get row no.
            selected_df = sales_over_time.iloc[selected_rowno, 0] # get cell

        cola, colb, colc = st.columns([4, 1, 5], vertical_alignment='center')
        with colc:
            if not selected_df.empty:
                selected_date = selected_df.iloc[0]
                transaction_of_date = filtered_data[filtered_data['date'] == selected_date][['image_file_path', 'item_number', 'description', 'quantity', 'retail']].reset_index(drop=True)
                colb.write(f":blue[Transactions on] **:blue[{selected_date}]**:")
                st.dataframe(transaction_of_date, column_config={"image_file_path": st.column_config.ImageColumn("Image"),
                                        "item_number": st.column_config.Column("Item Number"),
                                        "description": st.column_config.Column("Description"),
                                        "quantity": st.column_config.Column("Qty. Sold"),
                                        "retail": st.column_config.Column("Revenue")}, use_container_width=True, hide_index=True)

            # else:
                # selected_date = sales_over_time['date'][0]
                # transaction_of_date = filtered_data[filtered_data['date'] == selected_date][['image_file_path', 'item_number', 'description', 'quantity', 'retail']].reset_index(drop=True)
                # colb.write(f"**:blue[Transaction Records:]**")
                # st.dataframe(pd.DataFrame(columns=['Image', 'Item Number', 'Description', 'Qty. Sold', 'Revenue']), use_container_width=True, hide_index=True)
                # container = st.container(border=True)
                # with container: st.empty()
    else:
        st.write("No transaction records found.")

    if st.button("← Previous Page", key='customer_analysis_back_button_2'):
        u.go_back()


    u.scroll_to_top()