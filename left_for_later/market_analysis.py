import streamlit as st
import pandas as pd
import re

# Function to display market analysis
def display_market_analysis():
    st.title("Market Analysis")

    # Load the CSV file
    file_path = 'data/sales/ranked_sales.csv'
    sales_data = pd.read_csv(file_path)

    # Define a function to clean abbreviations in the description
    def clean_abbreviations(description):
        abbreviations = {
            'GD': 'GOLD',
            'SV': 'SILVER',
            'BZ': 'BRONZE',
            'MM': 'MM',  # no change needed, just to ensure correct handling
            'BLK': 'BLACK',
            'RD': 'RED',
            'BLU': 'BLUE',
            'GRN': 'GREEN',
            'SM': 'SMALL',
            'LRG': 'LARGE',
            'TRP': 'TROPHY',
            'MDL': 'MEDAL',
            'CUP': 'CUP',
            'PLQ': 'PLAQUE',
            'WD': 'WOOD',
            'GLS': 'GLASS',
            'MTL': 'METAL'
        }
        
        for abbr, full in abbreviations.items():
            description = description.replace(abbr, full)
        return description

    # Clean the descriptions in the sales data
    sales_data['DESCRIPTION'] = sales_data['DESCRIPTION'].apply(clean_abbreviations)    

    # Define the categories
    shapes = ['OVALISH', 'ROUND', 'TRIANGLE', 'RECTANGLE', 'SQUARE', 'DIAMOND', 'CLEAR', ]
    colors = ['RED', 'BLACK', 'BLUE', 'GREEN', 'GOLD', 'SILVER', 'BRONZE', 'WHITE', 'YELLOW']
    sizes = ['SMALL', 'LARGE']
    types = ['TROPHY', 'MEDAL', 'CUP', 'PLAQUE']
    materials = ['GOLD', 'SILVER', 'BRONZE', 'WOOD', 'GLASS', 'METAL']
    measures_pattern = r'\d+MM'
    sports = ['BALL', 'GOLF', 'GOLFER', 'JUMP', 'KICK', 'SOCCER', 'SWIMMER']
    nature = ['EARTH', 'FIREWORKS', 'FLAG', 'FLAGISH', 'FLAME', 'FLOWER', 'MOON', 'SUNFLOWER', 'SUNRAY', 'SUNRISE', 'WAVE', 'WAVEY', 'WHEAT']
    geometric_concepts = ['AREA', 'BLOCK', 'FACETS', 'LINE', 'SIDE', 'SIDES', 'STEM']

    # Function to categorize the descriptions
    def categorize_description(description):
        category = {
            'Shape': None,
            'Color': None,
            'Size': None,
            'Type': None,
            'Material': None,
            'Measures': None,
            'Sport': None,
            'Nature': None,
            'Geometric Concept': None
        }

        # Check for each category in the description
        for shape in shapes:
            if shape in description.upper():
                category['Shape'] = shape

        for color in colors:
            if color in description.upper():
                category['Color'] = color

        for size in sizes:
            if size in description.upper():
                category['Size'] = size

        for type_ in types:
            if type_ in description.upper():
                category['Type'] = type_

        for material in materials:
            if material in description.upper():
                category['Material'] = material

        measure_match = re.search(measures_pattern, description.upper())
        if measure_match:
            category['Measures'] = measure_match.group()

        for sport in sports:
            if sport in description.upper():
                category['Sport'] = sport

        for item in nature:
            if item in description.upper():
                category['Nature'] = item

        for concept in geometric_concepts:
            if concept in description.upper():
                category['Geometric Concept'] = concept

        return category


    # Apply the categorization function to each description
    categorized_data = sales_data['DESCRIPTION'].apply(categorize_description)
    categorized_df = pd.DataFrame(categorized_data.tolist())

    # Combine the categorized data with the original sales data
    sales_data = pd.concat([sales_data, categorized_df], axis=1)

    # Group by each category and calculate the total quantity sold for each category
    category_totals = {}
    for category in categorized_df.columns:
        category_totals[category] = sales_data.groupby(category)['QUANTITY'].sum()

    # Display the total sales for each category
    for category, totals in category_totals.items():
        st.write(f"### Total sales for {category}")
        st.write(totals.reset_index())