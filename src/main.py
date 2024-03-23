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

app_config_data = AppConfig()

st.set_page_config(
    page_title="Satellite Image Viewer",
    page_icon=":satellite:",
    layout="wide",
)

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
    # Define the geographic and projected coordinate reference systems
    geographic_crs = pyproj.CRS("EPSG:4326")  # WGS84
    projected_crs = pyproj.CRS("EPSG:3857")

    # Convert GeoJSON dictionary to a shapely geometry object
    geometry = shape(geojson_dict['geometry'])

    # Define the transformation function from geographic to projected CRS
    project = pyproj.Transformer.from_crs(geographic_crs, projected_crs, always_xy=True).transform

    # Project the geometry to the projected CRS
    projected_geometry = transform(project, geometry)

    # Compute the area of the projected geometry
    area = projected_geometry.area

    return area/10_000

def create_download_image_button(image_data):
    with io.BytesIO() as buffer:
        # Write array to buffer
        image_data = Image.fromarray((image_data*255).astype(np.uint8))
        image_data.save(buffer, format='JPEG')
        btn = st.download_button(
            label="Download image",
            data = buffer, # Download buffer
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
        data = json.dumps(feature), # Download buffer
        file_name = 'sentinel2_polygon.geojson',
        mime="application/json"
    )

def startup_session_variables():
    if "image_data" not in st.session_state:
        st.session_state["image_data"] = {}
    if "geometry" not in st.session_state:
        st.session_state["geometry"] = {}
    if "update_map" not in st.session_state:
        st.session_state["update_map"] = False
    if "area_too_big" not in st.session_state:
        st.session_state["area_too_big"] = False
    if "area_too_big_value" not in st.session_state:
        st.session_state["area_too_big_value"] = 0
    if "end_date" not in st.session_state:
        st.session_state["end_date"] = datetime.now()
    if "start_date" not in st.session_state:
        st.session_state["start_date"] = datetime(2015, 6, 22)
    if "date_range_value" not in st.session_state:
        st.session_state["data_range_value"] = (
            st.session_state["end_date"] - timedelta(days=365),
            st.session_state["end_date"])

def main():
    web_map = WebMap()
    web_map.add_draw_support()
    web_map.add_base_map(app_config_data.google_basemap, "google satellite", "google")
    web_map.add_base_map(app_config_data.esri_basemap, "esri satellite", "esri")

    st.title("Stealth Satellite Image Viewer")
    st.write("Draw polygon on map to get recent Sentinel 2 image")
    st.write("Be cool no logs enabled, stealth search your image ;)")

    startup_session_variables()

    # Create a datetime slider with custom format and options
    col1, col2 = st.columns(2)
    render_mosaic = st.checkbox("Render mosaic", value=True)
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
        max_cloud_percent = st.slider("Maximum cloud cover", min_value=0, max_value=100, value=60, step=5)

    if st.session_state["area_too_big"]:
        st.write(f":red[Area too big ({st.session_state['area_too_big_value']:.2f}ha), draw smaller box, maximum={app_config_data.max_area_hectares:.2f}ha]")

    if st.session_state["image_data"] != {}:
        st.write(f'Image ID: {st.session_state["image_data"]["name"]}')
        # Create an in-memory buffer
        col1, col2 = st.columns(2)
        with col1:
            create_download_image_button(st.session_state["image_data"]["image"])
        with col2:
            properties = {
                "image_bounds": st.session_state["image_data"]["bounds"],
                "image_id": st.session_state["image_data"]["name"]
            }
            create_download_geojson_button(st.session_state["geometry"], properties)
        web_map.add_image(
            st.session_state["image_data"]["image"],
            st.session_state["image_data"]["bounds"],
            "sentinel 2 image",
            )
        web_map.add_polygon(st.session_state["geometry"])

    if st.session_state["geometry"] != {} \
        and st.session_state["update_map"] == True:

        stac_items = catalog_search(
            app_config_data.stac_url,
            st.session_state["geometry"],
            date_string,
            max_cloud_percent
        )
        image_data = render_image(stac_items, st.session_state["geometry"], render_mosaic)

        st.session_state["image_data"] = image_data
        st.session_state["update_map"] = False

    web_map.add_layer_control()
    user_draw = web_map.render_web_map()

    if user_draw["geometry"] != None:
        area_user_draw = compute_area_hectares(user_draw)
        if area_user_draw >= app_config_data.max_area_hectares:
            st.session_state["area_too_big"] = True
            st.session_state["area_too_big_value"] = area_user_draw
            st.rerun()
            return

    if user_draw["geometry"] != None \
        and user_draw["geometry"] != st.session_state["geometry"]:
        st.session_state["area_too_big"] = False
        st.session_state["geometry"] = user_draw["geometry"]
        st.session_state["update_map"] = True
        st.rerun()

    st.write("[Code on GitHub](https://github.com/rupestre-campos/satellite-image-viewer)")
    return True

if __name__ == "__main__":
    main()