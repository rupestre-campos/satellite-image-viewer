# satellite image viewer
Simple app to show recent satellite images

## Instalation
How to run in debian based distros
´´´
# Python 3.10
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

streamlit run src/main.py
´´´

## Development
How to run tests
´´´
# Python 3.10
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt

pytest tests/
´´´
