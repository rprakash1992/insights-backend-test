1. Create a python virtual environment by running `python -m venv .venv`.
2. Activate the python virtual environment by running `.\.venv\Scripts\activate`.
3. Upgrade pip by running `python -m pip install --upgrade pip`.
4. Install the dependencies by running `pip install -r .\requirements.txt`.
5. Run the fastapi backend application by running `uvicorn vcti.app.insights.app:app --port 8080`.