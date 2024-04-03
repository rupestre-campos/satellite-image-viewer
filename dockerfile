FROM python:3.10-slim

WORKDIR /src

COPY ./src /src
COPY requirements.txt /src

RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

EXPOSE 8001

ENV STREAMLIT_SERVER_PORT=8001
ENV BUFFER_WIDTH=3000
ENV EMAIL_NOMINATIM="test-satellite-viewer@null.com"

ENV DEFAULT_CLOUD_COVER=30
ENV DEFAULT_SATELLITE_CHOICE_INDEX=0
ENV DEFAULT_START_ADDRESS="Baltimore"

ENV GDAL_CACHEMAX=200
ENV GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR
ENV GDAL_HTTP_MULTIPLEX=YES
ENV GDAL_HTTP_MERGE_CONSECUTIVE_RANGES=YES
ENV GDAL_BAND_BLOCK_CACHE=HASHSET
ENV GDAL_HTTP_MAX_RETRY=4
ENV GDAL_HTTP_RETRY_DELAY="0.42"
ENV CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.TIF,.tiff"
ENV CPL_VSIL_CURL_CACHE_SIZE=200000000
ENV VSI_CACHE=TRUE
ENV VSI_CACHE_SIZE=5000000
ENV GDAL_HTTP_VERSION=2
ENV PROJ_NETWORK=OFF

ENV ENABLE_LANDSAT=FALSE
ENV LANDSAT_AWS_SECRET_ACCESS_KEY=yoursecret
ENV LANDSAT_AWS_ACCESS_KEY_ID=yourid
ENV LANDSAT_AWS_NO_SIGN_REQUESTS=NO
ENV LANDSAT_AWS_REQUEST_PAYER=requester
ENV LANDSAT_AWS_REGION_NAME="us-west-2"

CMD ["streamlit", "run", "main.py"]