import streamlit as st
import pandas as pd
import json
from urllib.parse import unquote

# App code
def load_data(file_path):
    data = pd.read_csv(file_path)
    data['Date'] = pd.to_datetime(data['Date'], dayfirst=True)
    return data

def safe_json_loads(json_str):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def extract_levels(json_data, level_name):
    if json_data:
        for item in json_data:
            if item['name'] == level_name:
                return item['value']
    return None

def filter_farms(data):
    return data['farmName'].unique()

def display_farm_info(data, farm_name):
    farm_data = data[data['farmName'] == farm_name]
    for index, row in farm_data.iterrows():
        col1, col2 = st.columns(2)
        with col1:
            st.image(row['Image URL'], caption=f"Image {index + 1}", use_column_width=True)
        with col2:
            st.write("Farm Name:", row['farmName'])
            st.write("Other Information:")
            try:
                json_data = json.loads(row['json data'])
            except json.JSONDecodeError:
                json_data = []
            for item in json_data:
                st.write(f"{item['name']}: {item['value']}")
            st.write("#### Activity ")
            st.write(row['activity_record'])
            st.write('##### Activity Date')
            st.write(row['Date'])

st.set_page_config(layout="wide")
st.title("Farm Information Dashboard")
uploaded_file = "https://raw.githubusercontent.com/sakshamraj4/abinbev/main/test1.csv"

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)

    if 'json data' not in data.columns:
        st.error("The 'json data' column is not present in the uploaded file.")
    else:
        data['json_data'] = data['json data'].apply(safe_json_loads)
        data = data.dropna(subset=['json_data'])

        data['Severity'] = data['json_data'].apply(lambda x: extract_levels(x, 'Severity'))

        farms = filter_farms(data)

        query_params = st.experimental_get_query_params()
        farm_name_param = query_params.get('farm_name', [None])[0]
        severity_param = query_params.get('Severity', [None])[0]

        if farm_name_param:
            farm_name_param = unquote(farm_name_param)
            st.write(f"Decoded farm_name_param: {farm_name_param}")  # Debugging line

        if farm_name_param and severity_param:
            severity_param = unquote(severity_param)
            farm_name_param = unquote(farm_name_param)
            st.write(f"Decoded severity_param: {severity_param}")  # Debugging line
            
        else:
            default_farm_index = 0

        selected_farm = st.sidebar.selectbox("Select Farm", farms, index=default_farm_index)

        severity_levels = ['Select All'] + list(data['Severity'].dropna().unique())


        # Move the severity selectbox outside the condition to ensure it is always displayed correctly
        selected_severity = st.sidebar.selectbox("Severity", severity_levels, index=default_severity_index)

        if selected_farm:
            if selected_severity == 'Select All':
                filtered_data = data[data['farmName'] == selected_farm]
            else:
                filtered_data = data[(data['farmName'] == selected_farm) & (data['Severity'] == selected_severity)]

            display_farm_info(filtered_data, selected_farm)
