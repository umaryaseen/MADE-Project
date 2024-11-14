# Project Plan

## Title
<!-- Give your project a short title. -->
MADE project

## Main Question
1. How has the adoption of electric vehicles influenced energy grids and infrastructure development in North American cities?

## Description

This data engineering project aims to analyze the impact of electric vehicle (EV) adoption on energy grids and infrastructure development in North American cities. With the rise of EVs, there is a surging need to understand how increased electricity demand affects existing energy infrastructure and what steps cities are taking to accommodate this shift. By examining this relationship, the project seeks to provide insights that can aid policymakers, utility companies, and urban planners in making informed decisions.

To accomplish this, I will utilize EV adoption rates from the International Energy Agency to identify trends in electric vehicle usage across different cities. Energy consumption data from utility companies will be integrated to assess how these adoption rates correlate with changes in electricity demand and grid load patterns. Additionally, infrastructure development plans from city governments will be analyzed to determine how municipalities are responding in terms of upgrading grids, building charging stations, and investing in renewable energy sources.

The methodology involves data cleaning and integration to create a cohesive dataset for analysis. Statistical methods and data visualization tools will be employed to uncover patterns and relationships. By synthesizing these diverse data sources, the project aims to paint a comprehensive picture of the challenges and developments prompted by the surge in EV adoption.

## Datasources

<!-- Describe each datasources you plan to use in a section. Use the prefic "DatasourceX" where X is the id of the datasource. -->

### Datasource1: Global EV Outlook 2024
* Data URL: https://huggingface.co/datasets/cfahlgren1/us-ev-charging-locations/blob/main/charging_stations.json
* Data Type: JSON

* Data URL: https://www.kaggle.com/datasets/salvatoresaia/ev-charging-stations-us/data
* Data Type: xlsx



The Global EV Outlook is an annual publication that identifies and discusses recent developments in electric mobility across the globe. It is developed with the support of the members of the Electric Vehicles Initiative (EVI).


## Work Packages
<!-- List of work packages ordered sequentially, each pointing to an issue with more details. -->

1. Import and convert data from JSON [#1]
2. Identify the relevant columns and filter data in the transformation process [#2]
3. Clean up data with the pipeline [#3]
4. Store transformed data to SQLite database [#4]
5. Handle erros while using xlsx dataset [#5]

