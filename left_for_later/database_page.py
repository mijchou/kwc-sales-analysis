import streamlit as st
import pandas as pd
from datetime import timedelta
import utils as u

# Function to display the database page contents
def display_database(accounts_df, items_df, sales_data, selected_suppliers, selected_categories):

    col1, col2, col3 = st.columns([0.3, 0.3, 0.4])
    col1.title("Catalogue")

    # Filter the items and sales data by the selected suppliers and categories
    if selected_suppliers:
        items_df = items_df[items_df['supplier'].isin(selected_suppliers)]
    if selected_categories:
        items_df = items_df[items_df['category'].isin(selected_categories)]

    filtered_sales_data = sales_data[sales_data['item_number'].isin(items_df['item_number'])]

    # Calculate the quantity sold and total revenue per item number in the filtered date range
    sales_summary = filtered_sales_data.groupby('item_number').agg({'quantity': 'sum', 'retail': 'sum'}).reset_index()
    
    # Merge the sales summary with the items_df to get descriptions
    ranked_sales = pd.merge(items_df[['item_number', 'description', 'category', 'supplier']],
                            sales_summary[['item_number', 'quantity', 'retail']], on='item_number', how='left')

    # Add sorting options
    sorting_options = {
        "Total Revenue": "retail",
        "Item Number": "item_number",
        "Description": "description",
        "Quantity Sold": "quantity"
    }
    sort_by = col2.selectbox("Sort by", options=list(sorting_options.keys()), index=0)

    # Sort the dataframe based on the selected option
    ranked_sales = ranked_sales.sort_values(by=sorting_options[sort_by], ascending=False)

    # Update the session state with the new ranked_sales dataframe
    st.session_state.df = ranked_sales[['item_number', 'description', 'category', 'supplier', 'retail', 'quantity']]

    # Use toggle to switch between table and images
    on = st.toggle("Switch to table")

    # With table
    if on:       
        st.dataframe(st.session_state.df, use_container_width=True, height=400)  # Adjust height as needed

        # # Add "More Details" button
        # if st.button("More Details", key="more_details"):
        #     st.session_state.current_page = "Sales Analysis"
        #     st.session_state.selected_item_number = item_number
        #     st.session_state.date_start = st.session_state.date_start
        #     st.session_state.date_end = st.session_state.date_end
        #     st.experimental_rerun()
    else:
        # Display item gallery
        st.write("### Item Gallery")

        # Create a grid layout
        num_columns = 4  # Define the number of columns for the gallery
        columns = st.columns(num_columns)

        for i, item in enumerate(ranked_sales['item_number']):
            col = columns[i % num_columns]
            with col:
                image_path = u.find_image_path(item)
                if image_path:
                    st.image(image_path, use_column_width=True, caption=item)
                else:
                    st.write(f"No image for {item}")
