import streamlit as st

from app_config import AppConfig
from view.web_map import WebMap
from controller.image_renderer import ImageRenderer
from controller.catalog_searcher import CatalogSearcher
from controller.address_searcher import AddressSearcher
from controller.point_bufferer import PointBufferer

from datetime import datetime, timedelta

app_config_data = AppConfig()

st.set_page_config(
    page_title="Satellite Image Viewer",
    page_icon=":satellite:",
    layout="wide",
)
worker_catalog_searcher = CatalogSearcher(app_config_data.stac_url)
worker_image_renderer = ImageRenderer()
worker_point_bufferer = PointBufferer()
worker_address_searcher = AddressSearcher(
    user_agent=app_config_data.geocoder_user_agent
)

@st.cache_data
def buffer_point(latitude, longitude, distance):
    return worker_point_bufferer.buffer(latitude, longitude, distance)

@st.cache_data
def search_place(address):
    if not address:
        return None
    location = worker_address_searcher.search_address(address)
    return location

@st.cache_data
def catalog_search(max_items, feature_geojson, date_string, max_cloud_cover, collection, platforms):
    params = {
        "feature_geojson": feature_geojson,
        "date_string": date_string,
        "max_cloud_cover": max_cloud_cover,
        "max_items": max_items,
        "collection": collection,
        "platforms": platforms
    }

    return worker_catalog_searcher.search_images(params)

@st.cache_data
def mosaic_render(stac_list, geojson_geometry, satellite_params):
    params = satellite_params.copy()
    params.update({
        "zip_file": True,
        "image_format": "PNG",
        "geojson_geometry": geojson_geometry,
        "stac_list": stac_list,
        "image_as_array": True
    })

    image_data = worker_image_renderer.render_mosaic_from_stac(params)
    return image_data

def create_download_zip_button(zip_file, name):
    zip_name = name[:128].replace(',','-')
    st.download_button(
        label="Download data",
        data = zip_file,
        file_name = f"{zip_name}.zip",
        mime="application/octet-stream"
    )

def create_datestring_from_selected_dates(selected_dates):
    start_date = selected_dates[0].strftime('%Y-%m-%d')
    end_date = selected_dates[1].strftime('%Y-%m-%d')
    return f"{start_date}/{end_date}"

def parse_location(location):
    warning = ""
    latitude = 0
    longitude = 0
    if location:
        latitude = location[0]
        longitude = location[1]
        return {
            "latitude": latitude,
            "longitude": longitude,
            "warning": warning
        }
    warning = "Location not found."
    return  {
        "latitude": latitude,
        "longitude": longitude,
        "warning": warning
    }

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
    if "date_range_values" not in st.session_state:
        st.session_state["data_range_values"] = (
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

    satellite_sensor = st.radio(
        "Satellite",
        options=sorted(list(app_config_data.satelites.keys())),
        index=app_config_data.default_satellite_choice_index
    )
    satellite_sensor_params = app_config_data.satelites.get(satellite_sensor)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["start_date"] = datetime.strptime(
            satellite_sensor_params.get("start_date"),
            "%Y-%m-%d"
        )
        st.session_state["end_date"] = datetime.strptime(
            satellite_sensor_params.get("end_date"),
            "%Y-%m-%d"
        )
        selected_dates = st.slider(
            "Select a date range",
            min_value=st.session_state["start_date"],
            max_value=st.session_state["end_date"],
            value=st.session_state["data_range_values"],
            step=timedelta(days=1),
            format="YYYY-MM-DD"
        )
        st.session_state["data_range_values"] = selected_dates
        date_string = create_datestring_from_selected_dates(selected_dates)
    with col2:
        max_cloud_percent = st.slider(
            "Maximum cloud cover",
            min_value=0.0,
            max_value=100.0,
            value=app_config_data.default_cloud_cover,
            step=0.5
        )
    warning_area_user_input_location = st.empty()
    warning_area_user_input = st.empty()

    if address_to_search != st.session_state["where_to_go"]:
        st.session_state["where_to_go"] = address_to_search
        location = search_place(address_to_search)
        parsed_location = parse_location(location)
        if parsed_location["warning"]:
            warning_area_user_input_location.write(f":red[Location not found, try different keywords]")

        st.session_state["geometry"] = buffer_point(
                parsed_location["latitude"],
                parsed_location["longitude"],
                app_config_data.buffer_width
            )

    stac_items = catalog_search(
        app_config_data.max_stac_items,
        st.session_state["geometry"],
        date_string,
        max_cloud_percent,
        satellite_sensor_params["collection_name"],
        satellite_sensor_params["platforms"]
    )

    if len(stac_items) == 0:
        warning_area_user_input.write(f":red[Search returned no results, change date or max cloud cover]")
    if len(stac_items) > 0:
        image_data = mosaic_render(stac_items, st.session_state["geometry"], satellite_sensor_params)

        st.write(f'Image ID: {image_data["name"]}')

        col1, col2 = st.columns(2)
        with col1:
            create_download_zip_button(image_data["zip_file"], image_data["name"])

        web_map.add_image(
            image_data["image"],
            image_data["bounds"],
            satellite_sensor_params["name"],
            )

        web_map.add_polygon(st.session_state["geometry"])

    web_map.add_layer_control()
    user_draw = web_map.render_web_map()

    if user_draw["geometry"] != None \
        and st.session_state["user_draw"] != user_draw["geometry"]:
        st.session_state["user_draw"] = user_draw["geometry"]
        longitude = user_draw["geometry"]["coordinates"][0]
        latitude = user_draw["geometry"]["coordinates"][1]
        st.session_state["geometry"] = buffer_point(latitude, longitude, app_config_data.buffer_width)
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