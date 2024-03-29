import json
import pyproj
import numpy as np
import streamlit as st

from app_config import AppConfig
from view.web_map import WebMap
from controller.image_renderer import ImageRenderer
from controller.catalog_searcher import CatalogSearcher
from datetime import datetime, timedelta
from shapely.geometry import shape
from shapely.ops import transform

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import io
from PIL import Image

app_config_data = AppConfig()

st.set_page_config(
    page_title="Satellite Image Viewer",
    page_icon=":satellite:",
    layout="wide",
)

geolocator = Nominatim(
    timeout=3,
    user_agent=f"satellite-image-viewer+{app_config_data.email}"
)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)

geographic_crs = pyproj.CRS("EPSG:4326")
projected_crs = pyproj.CRS("EPSG:3857")
project_4326_to_3857 = pyproj.Transformer.from_crs(geographic_crs, projected_crs, always_xy=True).transform
project_3857_to_4326 = pyproj.Transformer.from_crs(projected_crs, geographic_crs, always_xy=True).transform


def do_geocode(address, attempt=1, max_attempts=5):
    try:
        return geolocator.geocode(address)
    except GeocoderUnavailable:
        if attempt <= max_attempts:
            return do_geocode(address, attempt=attempt+1)
        raise Exception("Too many searches")
    except GeocoderTimedOut:
        if attempt <= max_attempts:
            return do_geocode(address, attempt=attempt+1)
        raise Exception("Too many searches")

@st.cache_data
def search_place(address):
    if not address:
        return None
    location = do_geocode(address)

    return (location.latitude, location.longitude)

@st.cache_data
def catalog_search(stac_url, geometry, date_string, max_cloud_cover):
    catalog_worker = CatalogSearcher(
        stac_url,
        feature_geojson=geometry,
        date_string=date_string,
        max_cloud_cover=max_cloud_cover
    )
    return catalog_worker.search_images()

@st.cache_data
def image_render(stac_item, geometry):
    renderer = ImageRenderer(stac_item=stac_item, geojson_geometry=geometry)
    image_data = renderer.render_image_from_stac()
    return image_data

@st.cache_data
def mosaic_render(stac_list, geometry):
    renderer = ImageRenderer(stac_list=stac_list, geojson_geometry=geometry)
    image_data = renderer.render_mosaic_from_stac(zip_file=True)
    image_read = io.BytesIO(image_data["image"])
    image_read = Image.open(image_read)
    image_data["image"] = np.asarray(image_read)

    return image_data

def compute_area_hectares(geojson_dict):
    if not geojson_dict:
        return None

    geometry = shape(geojson_dict["geometry"])
    projected_geometry = transform(project_4326_to_3857, geometry)
    area = projected_geometry.area

    return area/10_000

def reproject(point, from_epsg, to_epsg):
    transformer = pyproj.Transformer.from_crs(from_epsg, to_epsg, always_xy=True)
    lon, lat = transformer.transform(point.x, point.y)
    return Point(lon, lat)

def buffer_point(point, buffer_distance):
    return point.buffer(buffer_distance)
    # Calculate half distance to form a square
    half_distance = buffer_distance / 2

    # Create vertices of the square
    left_bottom = Point(point.x - half_distance, point.y - half_distance)
    left_top = Point(point.x - half_distance, point.y + half_distance)
    right_bottom = Point(point.x + half_distance, point.y - half_distance)
    right_top = Point(point.x + half_distance, point.y + half_distance)

    # Create a polygon from the vertices
    square = Polygon([left_bottom, left_top, right_top, right_bottom])

    return square

def buffer_area(latitude, longitude, buffer_distance=100):
    input_point = Point(longitude, latitude)
    input_point_3857 = transform(project_4326_to_3857, input_point)
    buffered_point = buffer_point(input_point_3857, buffer_distance)
    buffered_point_4326 = transform(project_3857_to_4326, buffered_point)
    return json.dumps(Polygon(buffered_point_4326).__geo_interface__)


def create_download_zip_button(zip_file, name):
    zip_name = name[:128].replace(',','-')
    btn = st.download_button(
        label="Download data",
        data = zip_file,
        file_name = f"{zip_name}.zip",
        mime="application/octet-stream"
    )

def startup_session_variables():
    if "geometry" not in st.session_state:
        st.session_state["geometry"] = {}
    if "user_draw" not in st.session_state:
        st.session_state["user_draw"] = {}
    if "where_to_go" not in st.session_state:
        st.session_state["where_to_go"] = ""
    if "end_date" not in st.session_state:
        st.session_state["end_date"] = datetime.now()
    if "start_date" not in st.session_state:
        st.session_state["start_date"] = datetime(2015, 6, 22)
    if "date_range_value" not in st.session_state:
        st.session_state["data_range_value"] = (
            st.session_state["end_date"] - timedelta(days=365),
            st.session_state["end_date"])

def main():
    startup_session_variables()
    web_map = WebMap()

    web_map.add_draw_support()
    web_map.add_base_map(app_config_data.google_basemap, "google satellite", "google", show=True)
    web_map.add_base_map(app_config_data.open_street_maps, "open street maps", "open street maps")
    web_map.add_base_map(app_config_data.esri_basemap, "esri satellite", "esri")

    st.title("Satellite Image Viewer")
    st.write("Search where to go below or drop a pin on map to get fresh images")
    address_to_search = st.text_input("Search location", value=app_config_data.default_start_address)
    location = search_place(address_to_search)
    if address_to_search != st.session_state["where_to_go"]:
        st.session_state["where_to_go"] = address_to_search
        st.session_state["geometry"] = None

    col1, col2 = st.columns(2)

    with col1:
        selected_dates = st.slider(
            "Select a date range",
            min_value=st.session_state["start_date"],
            max_value=st.session_state["end_date"],
            value=st.session_state["data_range_value"],
            step=timedelta(days=1),
            format="YYYY-MM-DD"
        )
        st.session_state["data_range_values"] = selected_dates
        date_string = f"{selected_dates[0].strftime('%Y-%m-%d')}/{selected_dates[1].strftime('%Y-%m-%d')}"
    with col2:
        max_cloud_percent = st.slider("Maximum cloud cover", min_value=0, max_value=100, value=30, step=5)

    warning_area_user_input = st.empty()

    if not st.session_state["geometry"]:
        latitude = location[0]
        longitude = location[1]
        st.session_state["geometry"] = json.loads(
            buffer_area(latitude, longitude, app_config_data.buffer_width))

    stac_items = catalog_search(
        app_config_data.stac_url,
        st.session_state["geometry"],
        date_string,
        max_cloud_percent
    )
    if len(stac_items) == 0:
        warning_area_user_input.write(f":red[Search returned no results, change date or max cloud cover]")
    if len(stac_items) > 0:
        image_data = mosaic_render(stac_items, st.session_state["geometry"])

        st.write(f'Image ID: {image_data["name"]}')

        col1, col2 = st.columns(2)
        with col1:
            create_download_zip_button(image_data["zip_file"], image_data["name"])

        web_map.add_image(
            image_data["image"],
            image_data["bounds"],
            "sentinel 2 image",
            )

        web_map.add_polygon(st.session_state["geometry"])

    web_map.add_layer_control()
    user_draw = web_map.render_web_map()

    if user_draw["geometry"] != None \
        and st.session_state["user_draw"] != user_draw["geometry"]:
        st.session_state["user_draw"] = user_draw["geometry"]
        longitude = user_draw["geometry"]["coordinates"][0]
        latitude = user_draw["geometry"]["coordinates"][1]
        st.session_state["geometry"] = json.loads(
            buffer_area(latitude, longitude, app_config_data.buffer_width))
        st.rerun()
        return

    st.write("This application does not collect data but use carefully ;)")
    st.write("Made with:  STAC API from element84 to search images via pystac")
    st.write("rio_tiller to read and render STAC/COG links into a real image")
    st.write("folium/leaflet for the map and drawing")
    st.write("Open Street Maps and Nominatim to search addresses and street basemap")
    st.write("Satellite basemaps from google and esri")
    st.write("streamlit and streamlit cloud solution for UI and hosting")

    st.write("[Code on GitHub](https://github.com/rupestre-campos/satellite-image-viewer)")
    return True

if __name__ == "__main__":
    main()