import requests
import pandas as pd
import matplotlib.path as mplPath
import numpy as np
import sqlite3
import time


# Custom Exceptions
class PipelineError(Exception):
    """
    Custom exception for signaling an error within the pipeline.
    """
    pass


class EVChargingDataHandler:
    """
    Retrieves and processes EV charging station data.
    """
    def __init__(self, source_url=None, max_retries=3, backoff_factor=2):
        self.source_url = source_url or 'https://gold-flamingo-167771.hostingersite.com/data/us_ev_charging_stations_2024.json'
        self.records = None

        # Retry settings
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _download_data(self):
        """
        Fetch the charging station data from the specified URL with retry.
        """
        attempts = 0
        while attempts < self.max_retries:
            try:
                response = requests.get(self.source_url, timeout=10)
                response.raise_for_status()
                return response.json()
            except (requests.exceptions.RequestException, ValueError) as err:
                attempts += 1
                if attempts == self.max_retries:
                    raise ConnectionError(f"Unable to retrieve data from {self.source_url} after {self.max_retries} attempts. Error: {err}")
                else:
                    # Exponential backoff
                    sleep_time = self.backoff_factor ** attempts
                    print(f"Request failed (attempt {attempts}). Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)

    def _process_data(self):
        """
        Parse and prepare the EV charging station data.
        """
        try:
            raw_data = self._download_data()
            self.records = raw_data
        except Exception as e:
            raise PipelineError(f"Failed to process EV charging station data: {e}")

    def _clean_entries(self):
        """
        Clean and format the EV charging station data into a list of dictionaries 
        each containing 'latitude' and 'longitude' keys.
        """
        if not self.records:
            return []

        refined_data = []
        for entry in self.records:
            # Check for valid latitude and longitude
            if "lat" not in entry or "lng" not in entry or entry["lat"] is None or entry["lng"] is None:
                print(f"Ignoring invalid record: {entry}")
                continue
            refined_data.append({
                "latitude": entry["lat"],
                "longitude": entry["lng"]
            })
        return refined_data

    def get_charging_data(self):
        """
        Public method to initiate data retrieval and cleaning.
        Returns a list of charging station data records.
        """
        self._process_data()
        return self._clean_entries()


class CountyGeometryHandler:
    """
    Handles the geometry data for U.S. counties (in JSON format),
    converting each county into a Polygon or MultiPolygon object 
    for point-in-polygon checks.
    """
    def __init__(self, source_url=None, max_retries=3, backoff_factor=2):
        self.source_url = source_url or 'https://gold-flamingo-167771.hostingersite.com/data/gz_2010_us_050_00_20m.json'
        self.json_data = None
        self.geo_df = None

        # Retry settings
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _retrieve_data(self):
        """
        Fetch the geometry data from the specified URL with retry.
        """
        attempts = 0
        while attempts < self.max_retries:
            try:
                response = requests.get(self.source_url, timeout=10)
                response.raise_for_status()
                return response.json()
            except (requests.exceptions.RequestException, ValueError) as err:
                attempts += 1
                if attempts == self.max_retries:
                    raise ConnectionError(f"Unable to retrieve data from {self.source_url} after {self.max_retries} attempts. Error: {err}")
                else:
                    # Exponential backoff
                    sleep_time = self.backoff_factor ** attempts
                    print(f"Request failed (attempt {attempts}). Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)

    def _build_dataframe(self):
        """
        Convert the JSON geometry data into a pandas DataFrame
        and build Polygon/MultiPolygon objects.
        """
        try:
            data = self._retrieve_data()
            self.json_data = data
            dataframe = pd.DataFrame(data["features"])

            dataframe["Name"] = dataframe["properties"].apply(lambda x: x["NAME"])
            dataframe["ShapeType"] = dataframe["geometry"].apply(lambda x: x["type"])
            dataframe["CoordList"] = dataframe["geometry"].apply(lambda x: x["coordinates"])

            # Create a new dataframe for easier manipulation
            processed_df = pd.DataFrame()

            for _, row in dataframe.iterrows():
                shape_type = row["ShapeType"]
                coordinates = row["CoordList"]

                if shape_type == "MultiPolygon":
                    polygons = []
                    for coords_block in coordinates:
                        polygon_path = mplPath.Path(np.array(coords_block[0]))
                        polygons.append(polygon_path)
                    row["PolygonObject"] = polygons

                elif shape_type == "Polygon":
                    polygon_path = mplPath.Path(np.array(coordinates[0]))
                    row["PolygonObject"] = polygon_path

                else:
                    row["PolygonObject"] = None

                # Concatenate row results
                processed_df = pd.concat([processed_df, row], axis=1)

            # Reorient the concatenated df
            processed_df = processed_df.transpose()
            # Keep only relevant columns
            self.geo_df = processed_df.drop(columns=["type", "properties", "geometry", "CoordList"])
        except Exception as e:
            raise PipelineError(f"Failed to build geometry dataframe: {e}")

    def identify_county(self, latitude, longitude):
        """
        Given a latitude and longitude, identify which county (if any)
        contains that point.
        """
        if self.geo_df is None or self.geo_df.empty:
            print("Geometry DataFrame is empty. Make sure `load_geometry` was called successfully.")
            return None

        for _, row in self.geo_df.iterrows():
            poly_object = row["PolygonObject"]

            # Check if it is a MultiPolygon (list) or single Polygon
            if isinstance(poly_object, list):
                for single_polygon in poly_object:
                    # We try both (lat, long) and (long, lat)
                    if single_polygon.contains_point((latitude, longitude)) or single_polygon.contains_point((longitude, latitude)):
                        return row["Name"]
            else:
                if (poly_object is not None and 
                    (poly_object.contains_point((latitude, longitude)) or poly_object.contains_point((longitude, latitude)))):
                    return row["Name"]

        return None

    def load_geometry(self):
        """
        Public method to build the geometry dataset in memory.
        """
        self._build_dataframe()


class EVPopulationDataHandler:
    """
    Retrieves and processes data about the number of electric 
    and plug-in hybrid vehicles registered in each state.
    """
    def __init__(self, source_url=None, max_retries=3, backoff_factor=2):
        self.source_url = source_url or 'https://gold-flamingo-167771.hostingersite.com/data/updated_vehicle_registrations.json'
        self.population_data = None

        # Retry settings
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _fetch_population_data(self):
        """
        Download the EV population dataset from the specified URL with retry.
        """
        attempts = 0
        while attempts < self.max_retries:
            try:
                response = requests.get(self.source_url, timeout=10)
                response.raise_for_status()
                return response.json()
            except (requests.exceptions.RequestException, ValueError) as err:
                attempts += 1
                if attempts == self.max_retries:
                    raise ConnectionError(f"Unable to retrieve data from {self.source_url} after {self.max_retries} attempts. Error: {err}")
                else:
                    # Exponential backoff
                    sleep_time = self.backoff_factor ** attempts
                    print(f"Request failed (attempt {attempts}). Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)

    def _assemble_population_dict(self):
        """
        Convert the population dataset into a dictionary 
        mapping state -> total count of EV/PHEV.
        """
        raw_pop_data = self._fetch_population_data()
        results = {}
        for record in raw_pop_data:
            try:
                ev_count = int(record["Electric (EV)"].replace(",", "")) 
                phev_count = int(record["Plug-In Hybrid Electric (PHEV)"].replace(",", ""))
                total = ev_count + phev_count
                state_name = record["State"]
                results[state_name] = total
            except (KeyError, ValueError) as err:
                print(f"Invalid record in population data: {record} | Error: {err}")
        return results

    def get_population_data(self):
        """
        Public method to get the processed dictionary of EV/PHEV registrations.
        """
        try:
            self.population_data = self._assemble_population_dict()
        except Exception as e:
            raise PipelineError(f"Failed to assemble EV population data: {e}")
        return self.population_data


def store_results_in_sqlite(station_counts_by_state, ev_pop_data):
    """
    Creates a local SQLite database file named 'charging_station.db' 
    to store EV charging station counts alongside EV population counts for each state.
    """
    # Sort by state name for consistent insertion order
    sorted_data = dict(sorted(station_counts_by_state.items(), key=lambda x: x[0]))
    
    connection = sqlite3.connect('./data/charging_station.db')
    cursor = connection.cursor()

    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS charging_stations (
            state_name TEXT,
            count_of_ev_charging_stations INTEGER,
            count_of_ev_vehicles INTEGER
        );
    ''')

    # Insert data
    for state, station_count in sorted_data.items():
        vehicles_count = ev_pop_data.get(state, 0)
        cursor.execute(
            "INSERT INTO charging_stations (state_name, count_of_ev_charging_stations, count_of_ev_vehicles) "
            "VALUES (?, ?, ?);", 
            (state, station_count, vehicles_count)
        )

    connection.commit()
    connection.close()


class EVProjectPipeline:
    """
    Orchestrates the retrieval, processing, and storage of EV 
    charging station data, county geometries, and EV population data.
    """
    def __init__(self, max_pipeline_retries=2):
        """
        max_pipeline_retries: How many times to retry the entire pipeline if it fails unexpectedly.
        """
        # Handlers with default retry settings for data download
        self.charging_data_handler = EVChargingDataHandler()
        self.geometry_handler = CountyGeometryHandler()
        self.population_handler = EVPopulationDataHandler()

        # Pipeline retry
        self.max_pipeline_retries = max_pipeline_retries

    def run(self):
        """
        1. Load and clean the charging station data.
        2. Build the county geometry dataset.
        3. Retrieve and prepare the vehicle population data.
        4. Match charging stations to their respective states/counties and count them.
        5. Store the consolidated results in SQLite.
        """
        stations_per_state = {}

        # Pipeline attempts
        for attempt in range(1, self.max_pipeline_retries + 1):
            try:
                # Step 1: Charging Station Data
                station_data = self.charging_data_handler.get_charging_data()

                # Step 2: Geometry Data
                self.geometry_handler.load_geometry()

                # Step 3: EV Population Data
                ev_pop_data = self.population_handler.get_population_data()

                # Step 4: Match each charging station to its state/county
                for station in station_data:
                    # Attempt to identify the county/state of the station
                    county_or_state = self.geometry_handler.identify_county(
                        latitude=station["latitude"],
                        longitude=station["longitude"]
                    )
                    if county_or_state is not None:
                        stations_per_state[county_or_state] = stations_per_state.get(county_or_state, 0) + 1
                    else:
                        print(f"Could not match station to a state/county: {station}")

                # Step 5: Store results in a local SQLite database
                store_results_in_sqlite(stations_per_state, ev_pop_data)

                print("Pipeline completed successfully.")
                # If no exception, break from the retry loop.
                break

            except (PipelineError, ConnectionError) as pe:
                print(f"Pipeline attempt {attempt} failed with error: {pe}")
                if attempt == self.max_pipeline_retries:
                    print("Maximum pipeline retries reached. Exiting...")
                else:
                    # Wait before re-attempting the pipeline
                    wait_time = 3 * attempt
                    print(f"Retrying pipeline in {wait_time} seconds...")
                    time.sleep(wait_time)
            except Exception as e:
                print(f"Unexpected error during pipeline attempt {attempt}: {e}")
                if attempt == self.max_pipeline_retries:
                    print("Maximum pipeline retries reached. Exiting...")
                else:
                    wait_time = 3 * attempt
                    print(f"Retrying pipeline in {wait_time} seconds...")
                    time.sleep(wait_time)


if __name__ == "__main__":
    pipeline = EVProjectPipeline(max_pipeline_retries=3)
    pipeline.run()
