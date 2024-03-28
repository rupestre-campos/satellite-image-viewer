[![Python application](https://github.com/rupestre-campos/satellite-image-viewer/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/rupestre-campos/satellite-image-viewer/actions/workflows/python-app.yml)
# satellite image viewer
Simple app to show recent satellite images

## Demo app
You can test the demo hosted on streamlit [here](https://satellite-image-viewer.streamlit.app/).

## Instalation
How to run in debian based linux distros
Recomended Python version: Python 3.10 or above

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

streamlit run src/main.py
```

## Development
How to run tests
```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt

# install playright browser files
playwright install

# run tests
pytest tests/
```

## Docker build

```
docker build -t sat-img-view .
docker run -d --name sat-img-view-container -p 8001:8001 sat-img-view
docker start sat-img-view-container
```
