# Care-Load-and-Placements-Demand-for-HHS
# Streamlit Forecasting App

Quick instructions to run the Streamlit forecasting app for the Care Load dataset.

Prerequisites
- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run streamlit_app.py
```

Notes
- The app loads `HHS_Unaccompanied_Alien_Children_Program.csv` by default if no file is uploaded.
- Use the sidebar to pick the date and target column names, frequency, model and horizon.
- Models included: Naive, Moving Average, Exponential Smoothing.

