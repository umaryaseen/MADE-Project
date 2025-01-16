!/bin/bash
echo "Running pipeline.sh..."
# Install required packages from requirements.txt
pip install -r requirements.txt
python3 project/pipeline.py
echo "Pipeline completed successfully!"