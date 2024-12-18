import pandas as pd
import requests
from io import BytesIO

# Function to fetch and load data from the Excel file
def fetch_excel_data(url):
    """
    Fetches data from an Excel file at the given URL and returns it as a dictionary of DataFrames.
    
    :param url: str, URL to the Excel file
    :return: dict of DataFrames, where keys are sheet names
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        excel_data = pd.read_excel(BytesIO(response.content), sheet_name=None)
        return excel_data
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch Excel data: {e}")
        return None

# Function to fetch data from the API
def fetch_api_data(api_url, api_key, params):
    """
    Fetches data from the API using the given parameters and API key.
    
    :param api_url: str, base URL of the API
    :param api_key: str, API key for authentication
    :param params: dict, query parameters for the API
    :return: dict, parsed JSON response
    """
    try:
        params['api_key'] = api_key  # Add API key to parameters
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Ensure the request was successful
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch API data: {e}")
        return None

# Pipeline function to fetch data from both sources
def data_pipeline():
    """
    Executes the data pipeline to fetch data from the Excel file and API.
    
    :return: tuple, (Excel data as dict of DataFrames, API data as dict)
    """
    # Define the data sources
    excel_url = 'https://www.eia.gov/electricity/monthly/xls/table_d_1.xlsx'
    api_url = 'https://developer.nrel.gov/api/alt-fuel-stations/v1.json'
    api_key = 'sLEpeomveD6uGw802SbrAd2MNRccwFu5yaBIbVw8'  # Replace with your API key
    api_params = {
        format: 'xml',
    }
    
    # Fetch data
    excel_data = fetch_excel_data(excel_url)
    api_data = fetch_api_data(api_url, api_key, api_params)
    
    return excel_data, api_data

# Run the pipeline
if __name__ == "__main__":
    excel_data, api_data = data_pipeline()
    
    # Display a preview of the fetched data
    if excel_data:
        print("Excel Data Sheets:", excel_data.keys())  # Display sheet names
        print("Preview of First Sheet:", list(excel_data.values())[0].head())
    
    if api_data:
        stations_df = pd.DataFrame(api_data['fuel_stations'])
        print("API Data Preview:")
        print(stations_df)
