# Import necessary packages
import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import utils as u

import sales_overview as so
import sales_analysis as sa
import customer_analysis as ca
# import database_page as dp

# Set Streamlit page configuration
st.set_page_config(
    page_title="KWC Sales Analysis",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# app.py

st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 364px !important;
        }
        .sidebar-section {
            margin-bottom: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Define file paths
DATA_DIR = os.path.join(os.getcwd(), 'data')
SALES_FILE = os.path.join(DATA_DIR, 'sales/sales_cleaned.csv')
ITEMS_FILE = os.path.join(DATA_DIR, 'items/items.csv')
PURCHASE_RECORD_FILE = os.path.join(DATA_DIR, 'others/purchase_record.csv')
ACCOUNTS_FILE = os.path.join(DATA_DIR, 'accounts/accounts_df.csv')

# Load accounts data for mapping accno to full names
accounts_df = pd.read_csv(ACCOUNTS_FILE)
accounts_df['name'] = accounts_df['name'].str.title()  # Convert names to title case


@st.cache_data
def load_data():
    sales_data = pd.read_csv(SALES_FILE)
    sales_data['date'] = pd.to_datetime(sales_data['date'], format='%d/%m/%Y').dt.date
    items_df = pd.read_csv(ITEMS_FILE)
    purchase_record_df = pd.read_csv(PURCHASE_RECORD_FILE)
    purchase_record_df['date'] = pd.to_datetime(purchase_record_df['date'], format='%d/%m/%Y').dt.date
    return sales_data, items_df, purchase_record_df

def change_date(max_date, option=''):
    if option == "Week":
        st.session_state.date_start = max_date - timedelta(days=7)
        st.session_state.date_end = max_date
    elif option == "Month":
        st.session_state.date_start = max_date - relativedelta(months=1)
        st.session_state.date_end = max_date
    elif option == "Year":
        st.session_state.date_start = max_date - relativedelta(years=1)

def initialize_session_state(max_date):
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Sales Overview"
    # if 'area_key' not in st.session_state:
    #     st.session_state.area_key = 1
    if 'date_end' not in st.session_state:
        st.session_state.date_end = max_date
    if 'date_start' not in st.session_state:
        st.session_state.date_start = max_date - timedelta(days=183)
    if 'selectbox_category_key' not in st.session_state:
        st.session_state.selectbox_category_key = 0
    if 'selectbox_supplier_key' not in st.session_state:
        st.session_state.selectbox_supplier_key = 1
    if 'selectbox_item_key' not in st.session_state:
        st.session_state.selectbox_item_key = 1000
    if 'selectbox_customer_key' not in st.session_state:
        st.session_state.selectbox_customer_key = 2000
    if 'previous_page' not in st.session_state:
        st.session_state.previous_page = None

# Load data
sales_data, items_df, purchase_record_df = load_data()
max_date = sales_data['date'].max()

# Update the category column
# items_df = u.update_category(items_df)  # Uncomment this line when you load items_df

# Merge sales data with accounts and items data
sales_data = sales_data.merge(accounts_df[['accno', 'name', 'termcode', 'delimit', 'show',
                                            'addr1', 'addr2', 'addr3', 'code', 'disc', 'tel', 'contact', 'email']], on='accno', how='left')
sales_data = sales_data.merge(items_df[['item_number', 'description', 'supplier', 'category']], on='item_number', how='left')

# Initialize session state
initialize_session_state(max_date)

#### Begins

# To "Sales Overview":
if st.sidebar.button(":house: Back to Sales Overview", key="back_to_sales_overview"):
    u.back_to_sales_overview()

# st.sidebar.divider()

# Sidebar elements
st.sidebar.markdown('## Filter')

# Create columns for date range
col1, col2 = st.sidebar.columns(2)

with col1:
    date_start = st.date_input("Start Date:", key="date_start")
    date_start = pd.to_datetime(date_start, format='%d/%m/%Y')
with col2:
    date_end = st.date_input("End Date:", key="date_end")
    date_end = pd.to_datetime(date_end, format='%d/%m/%Y')

# Create buttons to set date ranges
but1, but2, but3 = st.sidebar.columns([3.34, 3.57, 3.09])

with but1:
    if st.button("Past Week", on_click=change_date, args=(max_date, "Week")):
        option = "Week"
with but2:
    if st.button("Past Month", on_click=change_date, args=(max_date, "Month")):
        option = "Month"
with but3:
    if st.button("Past Year", on_click=change_date, args=(max_date, "Year")):
        option = "Year"

# Create multiselection for categories
category_options = ["Crystal & Glass", "Metal & Plastic", "Metal Medals & Ribbons", "Resin"] #, "Others"]
selected_categories = st.sidebar.multiselect(label="Category", placeholder="Choose one or more categories.", options=category_options, key = st.session_state.selectbox_category_key) #, label_visibility='collapsed')

# Create multiselection for suppliers
supplier = st.sidebar.multiselect(
    label="Supplier", placeholder="Choose one or more suppliers.",
    # options=["CS", "HH", "HX", "JL", "LD", "ZJ", "RH", "XY", "Others"] #, label_visibility='collapsed'
    options=['CS', 'LD', 'JT', 'XY', 'JL', 'HX', 'ZJ', 'CR', 'DD', 'NZJ', 'ZY', 'LC', 'JH', 'GH', 'RH', 'KK'], #, 'Others']
    key = st.session_state.selectbox_supplier_key
)

# Create Search bar for items
st.sidebar.markdown('## Search')

# Filter items_df to include only active items
active_items_df = items_df[items_df['active'] == 'Y']

# Get the full list of active item numbers from active_items_df
item_numbers = active_items_df['item_number'].unique()
item_number = st.sidebar.selectbox(label="By Item Number", placeholder="Choose an item number.", options=item_numbers,
                                    index=None, key=st.session_state.selectbox_item_key) #, label_visibility='collapsed')

# Create Search bar for customers

# Filter accounts_df to include only customers with show='Y'
visible_accounts_df = accounts_df[accounts_df['show'] == 'Y']

# Get the full list of customer numbers from visible_accounts_df
customer_numbers = pd.Series(visible_accounts_df['accno'] + ' (' + visible_accounts_df['name'] + ')').unique()
customer_number = st.sidebar.selectbox(label="By Customer Number", options=customer_numbers, placeholder="Choose a customer.",
                                    index=None, key=st.session_state.selectbox_customer_key) #, label_visibility='collapsed')

# When an item is selected, link to the sales analysis page
if item_number:
    st.session_state.current_page = "Sales Analysis"
    st.session_state.selected_item_number = item_number

# When a customer is selected, link to the customer analysis page
if customer_number:
    selected_customer_number = customer_number.split(' ')[0]  # Extract the accno
    st.session_state.current_page = "Customer Analysis"
    st.session_state.selected_customer_number = selected_customer_number

# Add radio buttons to switch between quantity and revenue
st.sidebar.markdown("## Target")
selected_metric_option = st.sidebar.radio("Measure sales in:", options=["Quantity", "Revenue"], index=0, horizontal=True, label_visibility='collapsed')
if selected_metric_option=='Revenue':
    selected_metric_option = 'retail'
elif selected_metric_option=='Quantity':
    selected_metric_option = 'quantity'
st.session_state.metric_option = selected_metric_option

def reset_button():
    st.session_state.date_end = max_date
    st.session_state.date_start = max_date - timedelta(days=183)
    st.session_state.selectbox_category_key = st.session_state.selectbox_category_key+1
    st.session_state.selectbox_supplier_key = st.session_state.selectbox_supplier_key+1
    st.session_state.selectbox_item_key = st.session_state.selectbox_item_key+1
    st.session_state.selectbox_customer_key = st.session_state.selectbox_customer_key+1

# Add the "Clear" button to reset the selected item number
clear_button = st.sidebar.button(
    label='Clear Selections', on_click=reset_button)






# Page display logic
page_display_functions = {
    "Sales Overview": lambda: so.display_sales_overview(sales_data, accounts_df, purchase_record_df, items_df, st.session_state.date_start, st.session_state.date_end, supplier, selected_categories, st.session_state.metric_option),#, st.session_state.display_option),
    "Sales Analysis": lambda: sa.display_sales_analysis(sales_data, accounts_df, purchase_record_df, items_df, st.session_state.selected_item_number, st.session_state.date_start, st.session_state.date_end, st.session_state.metric_option),#, st.session_state.display_option),
    "Customer Analysis": lambda: ca.display_customer_analysis(sales_data, accounts_df, st.session_state.selected_customer_number, items_df, st.session_state.date_start, st.session_state.date_end, supplier, selected_categories, st.session_state.metric_option),#, st.session_state.display_option),
    "Catalogue": lambda: dp.display_database(accounts_df, items_df, sales_data, supplier, selected_categories)  # Pass supplier here
}

page_display_functions.get(st.session_state.current_page, lambda: st.write("Page not found"))()
