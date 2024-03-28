FROM python:3.10-slim

WORKDIR /src

COPY ./src /src
COPY requirements.txt /src

RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

EXPOSE 8001

ENV STREAMLIT_SERVER_PORT=8001
ENV BUFFER_WIDTH=3000
ENV EMAIL_NOMINATIM="test-satellite-viewer@null.com"

CMD ["streamlit", "run", "main.py"]
