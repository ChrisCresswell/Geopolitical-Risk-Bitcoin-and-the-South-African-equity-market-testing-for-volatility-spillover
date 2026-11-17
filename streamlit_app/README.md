# Geopolitical Risk, Bitcoin, and Spillover Effects in South African Markets

An interactive Streamlit showcase for the Honours research project.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Add to the existing GitHub repository

Copy the complete `streamlit_app` folder into the root of the thesis repository. Keep the folder name `streamlit_app` so the relative paths to `data/` and `assets/` remain unchanged.

## Deploy with Streamlit Community Cloud

1. Connect the GitHub account to Streamlit Community Cloud.
2. Create an app using the existing thesis repository and the `main` branch (or the branch where this folder is uploaded).
3. Set the app file path to `streamlit_app/app.py`.
4. Deploy. The resulting `streamlit.app` URL can then be added to the CV.

## Contents

- `app.py`: six-page research showcase.
- `data/`: selected Script 9 CSV result tables used by the app.
- `assets/`: thesis figures exported by Script 9.

## Data handling

This package intentionally does **not** include `Thesis_Data.xlsx` or raw daily Bloomberg-derived financial observations. It uses selected Script 9 result tables and thesis figures. Before making the app public, confirm that the included thesis outputs and figures are cleared for public display under the applicable data-use, university and co-author requirements.

## Research source code

For the R analysis scripts and methodology, see:

https://github.com/ChrisCresswell/Geopolitical-Risk-Bitcoin-and-the-South-African-equity-market-testing-for-volatility-spillover
