import streamlit as st

from app_config import AppConfig
from view.web_map import WebMap
from controller.image_renderer import ImageRenderer
from controller.catalog_searcher import CatalogSearcher

app_config_data = AppConfig()

st.set_page_config(
    page_title="Satellite Image Viewer",
    page_icon=":satellite:",
    layout="wide",
)

@st.cache_data
def catalog_search(stac_url, geometry):
    catalog_worker = CatalogSearcher(
        stac_url,
        feature_geojson=geometry
    )
    return catalog_worker.search_images()

@st.cache_data
def image_render(stac_item, geometry):
    renderer = ImageRenderer(stac_item, geometry)
    image_data = renderer.render_image_from_stac()
    return image_data

def startup_session_variables():
    if "image_data" not in st.session_state:
        st.session_state["image_data"] = {}
    if "geometry" not in st.session_state:
        st.session_state["geometry"] = {}
    if "update_map" not in st.session_state:
        st.session_state["update_map"] = False

def main():
    web_map = WebMap()
    web_map.add_draw_support()
    web_map.add_base_map(app_config_data.google_basemap, "google", "google", show=True)
    web_map.add_base_map(app_config_data.esri_basemap, "esri", "esri")

    st.title("Satellite Image Viewer")
    startup_session_variables()
    if st.session_state["image_data"] != {}:
        web_map.add_image(
            st.session_state["image_data"]["image"],
            st.session_state["image_data"]["bounds"],
            st.session_state["image_data"]["name"],
            )
        web_map.add_polygon(st.session_state["geometry"])

    if st.session_state["geometry"] != {} \
        and st.session_state["update_map"] == True:

        stac_items = catalog_search(
            app_config_data.stac_url,
            st.session_state["geometry"]
        )

        image_data = image_render(stac_items[0], st.session_state["geometry"])

        st.session_state["image_data"] = image_data
        st.session_state["update_map"] = False

    web_map.add_layer_control()
    user_draw = web_map.render_web_map()
    if user_draw["geometry"] != None \
        and user_draw["geometry"] != st.session_state["geometry"]:
        st.session_state["geometry"] = user_draw["geometry"]
        st.session_state["update_map"] = True
        st.rerun()

    return True

if __name__ == "__main__":
    main()