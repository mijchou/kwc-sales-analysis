import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re
import datetime as dt



def back_to_sales_overview():
    st.session_state.selectbox_item_key = st.session_state.selectbox_item_key+1
    st.session_state.selectbox_customer_key = st.session_state.selectbox_customer_key+1
    st.session_state.current_page = "Sales Overview"
    st.experimental_rerun()




def plot_stock_history(sales_data=None,
                        purchase_record_df=None,
                        accounts_df=None,
                        item_number=None,
                        items_df=None,
                        date_start=None,
                        date_end=None,
                        xrange=None,
                        yrange=None,
                        height=None,
                        show_accno=True,
                        title=None):
    # Get current stock count
    current_stock = items_df[items_df['item_number'] == item_number]['instock'].iloc[0]

    # Get the sales transactions for the item
    sales_transactions = sales_data[(sales_data['date'] >= date_start) & 
                                        (sales_data['date'] <= date_end) &
                                        (sales_data['item_number'] == item_number)][['date', 'quantity', 'accno']]

    # Get the purchase records for the item within the date range
    purchase_records = purchase_record_df[(purchase_record_df['date'] >= date_start) & 
                                        (purchase_record_df['date'] <= date_end) &
                                        (purchase_record_df['item_number'] == item_number)][['date', 'quantity']]
    purchase_records['accno'] = 'STOCK-IN'

    # Combine sales and purchase data
    sales_transactions['quantity'] = -sales_transactions['quantity']  # Sales reduce stock
    purchase_records['quantity'] = purchase_records['quantity']      # Purchases increase stock
    stock_changes = pd.concat([sales_transactions, purchase_records])

    # sum quantity by accno from the same date, to add up sales and returns
    stock_changes = stock_changes.groupby(['date', 'accno']).agg({'quantity': 'sum'}).reset_index()

    # Define the priority accno
    priority_accno = 'STOCK-IN'

    # Create a priority column, where the priority accno gets a higher priority (lower number)
    stock_changes['priority'] = stock_changes['accno'].apply(lambda x: 1 if x == priority_accno else 0)

    # Sort by date descending to count backwards
    stock_changes = stock_changes.sort_values(by=['date', 'priority'], ascending=False)
    # st.write(stock_changes)

    # Calculate cumulative stock backwards
    stock_changes['cumulative_quantity'] = stock_changes['quantity'].cumsum()

    # The cumulative stock starting from the current stock gives us the historical stock levels
    stock_changes['stock_count'] = current_stock - stock_changes['cumulative_quantity']

    # Correct the stock count by shifting back one date point
    stock_changes['stock_count'] = stock_changes['stock_count'].shift(1)
    stock_changes = stock_changes.fillna(current_stock)

    # Sort by date ascending for plotting
    stock_changes = stock_changes.sort_values(by='date', ascending=True).reset_index(drop=True)

    # Add customer names for hover info
    stock_changes = pd.merge(stock_changes, accounts_df[['accno', 'name']], on='accno', how='left')

    # Add stock in our out text
    def pos_sign(num):
        if num>0: return '+' + str(num)
        else: return str(num)
    stock_changes['stock_inout'] = stock_changes['quantity'].apply(pos_sign)

    # Fill name where accno is 'STOCK-IN'
    stock_changes['name'] = stock_changes['name'].fillna('')

    # sort to optimize readibility of graph
    stock_changes = stock_changes.sort_values(by=['date', 'priority', 'stock_count'], ascending=[False, False, True])

    ## Graph
    # Plot the stock count history with markers
    fig = px.line(stock_changes, x='date', y='stock_count', markers=True, title=title)
    fig.update_layout(xaxis_title='Date', yaxis_title='Stock Count', height=height, margin=dict(t=2, b=0), hoverlabel=dict(bgcolor="white", font_color='black', font_size=14))  # Adjust height here
    fig.update_xaxes(tickformat='%b %d')
    # Add customer codes (accno) above each point
    if show_accno == True:
        for idx, row in stock_changes.iterrows():
            accno = stock_changes[(stock_changes['date'] == row['date'])&(stock_changes['priority'] == row['priority'])&(stock_changes['accno'] == row['accno'])]['accno'].iloc[0]
            fig.add_annotation(x=row['date'], y=row['stock_count'], text=accno, showarrow=True, arrowhead=1, ax=0, ay=-20)

    # Format the date in the tooltip
    stock_changes['date_str'] = pd.to_datetime(stock_changes['date']).dt.strftime('%Y-%m-%d')

    # Add hover information with accno and name
    fig.update_traces(
        hovertemplate="<b>Account No.</b>: %{customdata[0]}<br><b>Name</b>: %{customdata[1]}<br><b>In/Out</b>: %{customdata[2]}<br><b>In Stock</b>: %{y}<br><b>Date</b>: %{customdata[3]}",
        customdata=stock_changes[['accno', 'name', 'stock_inout', 'date_str']].values
    )

    fig.update_xaxes(range=xrange)
    fig.update_yaxes(range=yrange)
    # config = {'displayModeBar': False}
    # fig.show(config=config)
    st.plotly_chart(fig, use_container_width=True)

    return stock_changes



# Function to go back to the previous page
def go_back():
    st.session_state.current_page, st.session_state.previous_page = (
            st.session_state.previous_page,
            st.session_state.current_page,
        )
    st.experimental_rerun()

def scroll_to_top():
    js = '''
    <script>
        window.parent.document.querySelector(".main").scrollTo({ top: 0, behavior: 'smooth' });
    </script>
    '''
    st.components.v1.html(js, height=0)