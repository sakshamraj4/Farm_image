import streamlit as st
import pandas as pd
import json
from urllib.parse import unquote
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import requests

# App code
def load_data(file_path):
    data = pd.read_csv(file_path)
    # Ensure 'Date' is converted to datetime
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce', dayfirst=True)
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

def download_image(url, filename):
    try:
        img_response = requests.get(url)
        img_response.raise_for_status()  # Check if the request was successful
        img = Image.open(BytesIO(img_response.content))
        buf = BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue(), filename
    except (requests.exceptions.RequestException, UnidentifiedImageError):
        # Skip the image if an error occurs
        return None, None

def display_farm_info(data, farm_name):
    images_to_download = []
    
    farm_data = data[data['farmName'] == farm_name]
    for index, row in farm_data.iterrows():
        col1, col2 = st.columns(2)
        with col1:
            st.image(row['Image URL'], caption=f"Image {index + 1}", use_column_width=True)
            # Convert date to string format if it is a datetime object
            if isinstance(row['Date'], pd.Timestamp):
                img_name = f"{row['farmName']}_{row['Date'].strftime('%Y-%m-%d')}_{index + 1}.jpg"
            else:
                img_name = f"{row['farmName']}_unknown_date_{index + 1}.jpg"
            img_data, img_filename = download_image(row['Image URL'], img_name)
            if img_data:  # Skip the download button if the image download was unsuccessful
                st.download_button(label="Download Image", data=img_data, file_name=img_filename, mime="image/jpeg")
                images_to_download.append((img_data, img_filename))
            
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
    
    return images_to_download

def create_zip(images, zip_filename="images.zip"):
    from zipfile import ZipFile
    
    buf = BytesIO()
    with ZipFile(buf, 'w') as zipf:
        for img_data, img_filename in images:
            zipf.writestr(img_filename, img_data)
    buf.seek(0)
    return buf, zip_filename

st.set_page_config(layout="wide")
st.title("Farm Information Dashboard")
uploaded_file = "https://raw.githubusercontent.com/sakshamraj4/abinbev/main/test1.csv"

if uploaded_file is not None:
    data = load_data(uploaded_file)  # Ensure correct datetime format

    if 'json data' not in data.columns:
        st.error("The 'json data' column is not present in the uploaded file.")
    else:
        data['json_data'] = data['json data'].apply(safe_json_loads)
        data = data.dropna(subset=['json_data'])

        data['Severity'] = data['json_data'].apply(lambda x: extract_levels(x, 'Severity'))

        farms = filter_farms(data)

        query_params = st.experimental_get_query_params()
        farm_name_param = query_params.get('farm_name', [None])[0]
        severity_param = query_params.get('severity', [None])[0]
        
        if farm_name_param:
            farm_name_param = unquote(farm_name_param)
        
        if severity_param:
            severity_param = unquote(severity_param)
        
        if farm_name_param and farm_name_param in farms:
            default_farm_index = list(farms).index(farm_name_param)
        else:
            default_farm_index = 0

        severity_levels = ['Select All'] + list(data['Severity'].dropna().unique())
        
        if severity_param and severity_param in severity_levels:
            default_severity_index = severity_levels.index(severity_param)
        else:
            default_severity_index = 0

        selected_farm = st.sidebar.selectbox("Select Farm", farms, index=default_farm_index)
        selected_severity = st.sidebar.selectbox("Severity", severity_levels, index=default_severity_index)

        if selected_farm:
            if selected_severity == 'Select All':
                filtered_data = data[data['farmName'] == selected_farm]
            else:
                filtered_data = data[(data['farmName'] == selected_farm) & (data['Severity'] == selected_severity)]

            images_to_download = display_farm_info(filtered_data, selected_farm)
            
            if images_to_download:
                zip_data, zip_filename = create_zip(images_to_download)
                st.sidebar.download_button(label="Download All Images", data=zip_data, file_name=zip_filename, mime="application/zip")
