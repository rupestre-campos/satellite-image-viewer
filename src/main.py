import streamlit as st

from app_config import AppConfig
from view.web_map import WebMap
from controller.image_renderer import ImageRenderer
from controller.catalog_searcher import CatalogSearcher
from datetime import datetime, timedelta
from shapely.geometry import shape
from shapely.ops import transform
import pyproj
import io
from PIL import Image
import numpy as np
import json
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from streamlit_searchbox import st_searchbox

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
    image_data = renderer.render_mosaic_from_stac()
    return image_data

def render_image(stac_items, geometry, render_mosaic):
    if render_mosaic:
        return mosaic_render(stac_items, geometry)
    return image_render(stac_items[0], geometry)

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


def create_download_image_button(image_data):
    with io.BytesIO() as buffer:
        # Write array to buffer
        image_data = Image.fromarray((image_data*255).astype(np.uint8))
        image_data.save(buffer, format='JPEG')
        btn = st.download_button(
            label="Download image",
            data = buffer,
            file_name = 'sentinel2.jpeg',
            mime="image/jpeg"
        )

def create_download_geojson_button(geometry, properties):
    feature = {
        "type": "Feature",
        "properties": properties,
        "geometry": geometry
    }

    btn = st.download_button(
        label="Download polygon",
        data = json.dumps(feature),
        file_name = 'sentinel2_polygon.geojson',
        mime="application/json"
    )

def startup_session_variables():
    if "geometry" not in st.session_state:
        st.session_state["geometry"] = {}
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

    address_to_search = st.text_input("Search location", value=app_config_data.default_start_address)
    location = search_place(address_to_search)
    if address_to_search != st.session_state["where_to_go"]:
        st.session_state["where_to_go"] = address_to_search
        st.session_state["geometry"] = None

    col1, col2 = st.columns(2)
    render_mosaic = True
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

    clear_draw = st.button("clear draw")
    if clear_draw:
        st.session_state["geometry"] = {}

    warning_area_user_input = st.empty()
    warning_area = st.empty()

    if not st.session_state["geometry"]:
        st.session_state["geometry"] = json.loads(
            buffer_area(location[0], location[1], app_config_data.buffer_width))

    stac_items = catalog_search(
        app_config_data.stac_url,
        st.session_state["geometry"],
        date_string,
        max_cloud_percent
    )
    if len(stac_items) == 0:
        warning_area_user_input.write(f":red[Search returned no results, change date or max cloud cover]")
    if len(stac_items) > 0:
        image_data = render_image(stac_items, st.session_state["geometry"], render_mosaic)

        st.write(f'Image ID: {image_data["name"]}')

        col1, col2 = st.columns(2)
        with col1:
            create_download_image_button(image_data["image"])
        with col2:
            properties = {
                "image_bounds": image_data["bounds"],
                "image_id": image_data["name"]
            }
            create_download_geojson_button(st.session_state["geometry"], properties)

        web_map.add_image(
            image_data["image"],
            image_data["bounds"],
            "sentinel 2 image",
            )

        web_map.add_polygon(st.session_state["geometry"])

    web_map.add_layer_control()
    user_draw = web_map.render_web_map()
    area_user_draw = 0
    if user_draw["geometry"] != None:
        area_user_draw = compute_area_hectares(user_draw)
    if 0 < area_user_draw <= app_config_data.max_area_hectares \
        and st.session_state["geometry"] != user_draw["geometry"]:
        st.session_state["geometry"] = user_draw["geometry"]
        st.rerun()

    if area_user_draw > app_config_data.max_area_hectares:
        warning_area_user_input.write(f":red[Polygon drawn area too big: {st.session_state['area_too_big_value']:.2f}ha]")
        warning_area.write(f":red[draw smaller box with max:  {app_config_data.max_area_hectares:.2f}ha]")

    st.write("this application does not collect data but use carefully ;)")

    st.write("[Code on GitHub](https://github.com/rupestre-campos/satellite-image-viewer)")
    return True

if __name__ == "__main__":
    main()