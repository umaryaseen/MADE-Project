#!/bin/bash

# tests.sh - Enhanced automated testing script for the data pipeline

# Remove existing output files
echo "Cleaning up old output files..."
rm -f ./data/charging_stations.sqlite
rm -f ./data/charging_stations.json

# Execute the data pipeline
echo "Executing data pipeline..."
python3 project/pipeline.py

# Capture the exit code of the pipeline execution
PIPELINE_EXIT_CODE=$?

if [ $PIPELINE_EXIT_CODE -ne 0 ]; then
    echo "Data pipeline execution failed with exit code $PIPELINE_EXIT_CODE."
    exit 1
fi

# Validate output files
OUTPUT_FILES=("./data/charging_stations.sqlite" "./data/charging_stations.json")
ALL_FILES_EXIST=true

for FILE in "${OUTPUT_FILES[@]}"; do
    if [ -f "$FILE" ]; then
        echo "Output file '$FILE' exists."
    else
        echo "Output file '$FILE' does not exist."
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = true ]; then
    echo "Test Passed: All output files have been created."
    exit 0
else
    echo "Test Failed: Some output files are missing."
    exit 1
fi
