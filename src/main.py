import streamlit as st

from app_config import AppConfig
from view.web_map import WebMap
from controller.image_renderer import ImageRenderer
from controller.catalog_searcher import CatalogSearcher
from controller.address_searcher import AddressSearcher
from controller.point_bufferer import PointBufferer
from controller.animation_creator import AnimationCreator
from datetime import datetime, timedelta

app_config_data = AppConfig()

st.set_page_config(
    page_title="Satellite Image Viewer",
    page_icon=":satellite:",
    layout="wide",
)
worker_catalog_searcher = CatalogSearcher(app_config_data.stac_url)
worker_image_renderer = ImageRenderer()
colormaps = sorted(worker_image_renderer.colormaps)
worker_point_bufferer = PointBufferer()
worker_address_searcher = AddressSearcher(
    api_url=app_config_data.geocoder_url,
    api_key=app_config_data.geocoder_api_key

)
worker_animation_creator = AnimationCreator(
    catalog_searcher=worker_catalog_searcher,
    image_renderer=worker_image_renderer
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
def create_gif(
    feature_geojson,
    date_string,
    max_cloud_cover,
    satellite_params,
    time_per_image,
    period_time_break,
    width,
    view_params
    ):
    satellite_view_params = satellite_params.copy()
    satellite_view_params.pop("assets")
    satellite_view_params.pop("expression")
    satellite_view_params.update(view_params)

    params = {
        "feature_geojson": feature_geojson,
        "date_string": date_string,
        "period_time_break": period_time_break,
        "time_per_image": time_per_image,
        "width": width,
        "height": width,
        "image_search":{
            "max_cloud_cover": max_cloud_cover,
            "collection": satellite_view_params["collection_name"],
            "platforms": satellite_view_params["platforms"]
        },
        "image_render": satellite_view_params
    }
    result = worker_animation_creator.create_gif(params)
    return result

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
def mosaic_render(
    stac_list,
    feature_geojson,
    satellite_params,
    view_params,
    image_range,
    color_formula,
    colormap
    ):
    params = satellite_params.copy()
    params.update({
        "zip_file": True,
        "image_format": "PNG",
        "feature_geojson": feature_geojson,
        "stac_list": stac_list,
        "image_as_array": True,
    })
    params.pop("assets")
    params.pop("expression")
    params.update(view_params)
    params.update({"min_value":image_range[0], "max_value":image_range[1]})
    params.update({"color_formula": color_formula, "colormap":colormap})

    image_data = worker_image_renderer.render_mosaic_from_stac(params)

    return image_data

def create_download_zip_button(zip_file, name):
    zip_name = name[:128].replace(',','-')
    st.download_button(
        label="Download Image data",
        data = zip_file,
        file_name = f"{zip_name}.zip",
        mime="application/octet-stream"
    )

def create_download_gif_button(gif_result):
    gif_name = f"result-{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    st.download_button(
        label="Download GIF",
        data = gif_result["image"],
        file_name = f"{gif_name}.gif",
        mime="image/gif"
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

def get_min_max_image_range(view_mode, satellite_sensor_params):
    if view_mode=="expression":
        return {
            "range":(-1.0,1.0),
            "default": (
                satellite_sensor_params["index_min_value"],
                satellite_sensor_params["index_max_value"]
            ),
            "step":0.05
        }
    return {
        "range": (0, 63535),
        "default": (
            satellite_sensor_params["min_value"],
            satellite_sensor_params["max_value"]
        ),
        "step":1
    }

def startup_session_variables():
    st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
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
    if not "result_gif_image" in st.session_state:
        st.session_state["result_gif_image"] = {}

def main():
    startup_session_variables()
    web_map = WebMap()

    web_map.add_draw_support()
    web_map.add_measure_control()
    web_map.add_base_map(app_config_data.google_basemap, "google satellite", "google", show=True)
    web_map.add_base_map(app_config_data.open_street_maps, "open street maps", "open street maps")
    web_map.add_base_map(app_config_data.esri_basemap, "esri satellite", "esri")

    st.title("Satellite Image Viewer")
    st.write("Search where to go below or drop a pin on map to get fresh images")
    address_to_search = st.text_input(
        "Search address or location",
        value=app_config_data.default_start_address,
        placeholder="Drake Park Bend OR"
    )
    with st.expander("options"):
        col1, col2 = st.columns(2)
        with col1:
            col3, col4 = st.columns(2)
            with col3:
                satellite_sensor = st.radio(
                    "Satellite",
                    options=sorted(list(app_config_data.satelites.keys())),
                    index=app_config_data.default_satellite_choice_index
                )
                pixelate_image = st.checkbox("Pixelated image?", value=True)

                satellite_sensor_params = app_config_data.satelites.get(satellite_sensor)
            with col4:
                view_mode = st.radio(
                    "Select image composition",
                    options=["assets", "expression"],
                    index=0
                )
                options = sorted(satellite_sensor_params[view_mode].keys())
                options_index = options.index("real-color (RGB)") if view_mode == "assets" else options.index("ndvi")
                selected_bands = st.selectbox(
                    "options",
                    options=options,
                    index=options_index
                )
                min_max_range = get_min_max_image_range(view_mode, satellite_sensor_params)
                image_range = st.slider(
                    "Image Min Max range",
                    min_value=min_max_range["range"][0],
                    max_value=min_max_range["range"][1],
                    value=min_max_range["default"],
                    step=min_max_range["step"]
                )

                view_param = {view_mode: satellite_sensor_params[view_mode][selected_bands]}

        with col2:
            max_cloud_percent = st.slider(
                "Maximum cloud cover (%)",
                min_value=0.0,
                max_value=100.0,
                value=app_config_data.default_cloud_cover,
                step=0.5
            )
            color_formula = ""
            colormap = ""

            if view_mode == "assets":
                col3, col4 = st.columns(2)
                with col3:
                    saturation = st.slider(
                        "image saturarion",
                        min_value=0.0,
                        max_value=app_config_data.max_saturation,
                        step=0.1,
                        value=satellite_sensor_params["color_formula_saturation"]
                    )
                    gamma = st.slider(
                        "image gamma",
                        min_value=0.0,
                        max_value=app_config_data.max_gamma,
                        step=0.1,
                        value=satellite_sensor_params["color_formula_gamma"]
                    )
                with col4:
                    sigmoidal = st.slider(
                        "image sigmoidal",
                        min_value=0.0,
                        max_value=app_config_data.max_sigmoidal,
                        step=0.5,
                        value=satellite_sensor_params["color_formula_sigmoidal"]
                    )
                    sigmoidal_gain = st.slider(
                        "image sigmoidal gain",
                        min_value=0.0,
                        max_value=app_config_data.max_sigmoidal_gain,
                        step=0.1,
                        value=satellite_sensor_params["color_formula_sigmoidal_gain"]
                    )
                color_formula = f"sigmoidal RGB {sigmoidal} {sigmoidal_gain} "\
                                f"gamma RGB {gamma} saturation {saturation}"
            if view_mode == "expression":
                colormap = st.selectbox(
                    "Image colormap",
                    options=colormaps,
                    index=colormaps.index("viridis")
                )

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
            point_buffer_width = st.slider(
                "Point buffer distance (m)",
                min_value=50,
                max_value=app_config_data.buffer_width,
                value=app_config_data.buffer_width,
            )
        col1, col2 = st.columns(2)
        with col1:
            create_gif_button = False
            gif_check_box = False
            if satellite_sensor_params["name"].lower() in app_config_data.allowed_gif_satellite:
                gif_check_box = st.checkbox("Create GIF", value=False)
            if gif_check_box:
                time_per_image = st.slider(
                    "Time per image (s)",
                    min_value=0.01,
                    max_value=3.0,
                    step=0.01,
                    value=app_config_data.gif_default_time_per_image
                )
                period_time_break = st.slider(
                    "Day interval",
                    min_value=30,
                    max_value=365,
                    value=app_config_data.gif_default_day_interval
                )

                image_size = st.slider(
                    "Image size (pixels)",
                    min_value=100,
                    max_value=512,
                    value=320
                )

                with col2:
                    create_gif_button = st.button("Render GIF")
                    if create_gif_button:
                        result_gif_image = create_gif(
                            feature_geojson=st.session_state["geometry"],
                            date_string=date_string,
                            max_cloud_cover=max_cloud_percent,
                            satellite_params=satellite_sensor_params,
                            time_per_image=time_per_image,
                            period_time_break=period_time_break,
                            width=image_size,
                            view_params=view_param
                        )
                        st.session_state["result_gif_image"] = result_gif_image
                        result_gif_image = None


    warning_area_user_input_location = st.empty()
    warning_area_user_input = st.empty()

    if address_to_search != st.session_state["where_to_go"]:
        st.session_state["where_to_go"] = address_to_search
        location = search_place(address_to_search)
        parsed_location = parse_location(location)
        if parsed_location["warning"]:
            warning_area_user_input_location.write(f":red[Location not found, try different keywords]")

        st.session_state["geometry"] = {
            "type": "Feature",
            "properties": {},
            "geometry": buffer_point(
                parsed_location["latitude"],
                parsed_location["longitude"],
                point_buffer_width
            )
        }
        st.session_state["result_gif_image"] = {}

    stac_items = catalog_search(
        app_config_data.max_stac_items,
        st.session_state["geometry"],
        date_string,
        max_cloud_percent,
        satellite_sensor_params["collection_name"],
        satellite_sensor_params["platforms"]
    )
    col1, col2 = st.columns(2)
    if len(stac_items) == 0:
        warning_area_user_input.write(f":red[Search returned no results, change date or max cloud cover]")
    if len(stac_items) > 0:
        image_data = mosaic_render(
            stac_items,
            st.session_state["geometry"],
            satellite_sensor_params,
            view_param,
            image_range,
            color_formula,
            colormap)

        st.write(f'Image ID: {image_data["name"]}')

        with col1:
            create_download_zip_button(image_data["zip_file"], image_data["name"])

        web_map.add_image(
            image_data["image"],
            image_data["bounds"],
            satellite_sensor_params["name"],
            )

        web_map.add_polygon(st.session_state["geometry"])
    with col2:
        if st.session_state["result_gif_image"]:
            create_download_gif_button(st.session_state["result_gif_image"])
    web_map.add_layer_control()
    user_draw = web_map.render_web_map(pixelated=pixelate_image)

    if user_draw["geometry"] != None \
        and st.session_state["user_draw"] != user_draw["geometry"]:
        st.session_state["user_draw"] = user_draw["geometry"]
        longitude = user_draw["geometry"]["coordinates"][0]
        latitude = user_draw["geometry"]["coordinates"][1]
        st.session_state["geometry"] = {
            "type": "Feature",
            "properties": {},
            "geometry": buffer_point(
                latitude,
                longitude,
                point_buffer_width
            )
        }
        st.session_state["result_gif_image"] = {}
        st.rerun()
        return

    st.write("This application does not collect data but use carefully ;)")
    st.write("Made with:  STAC API from element84 to search images via pystac")
    st.write("rio_tiller to read and render STAC/COG links into a real image")
    st.write("folium/leaflet for the map and drawing")
    st.write("Open Street Maps street basemap")
    st.write("[geocode](https://geocode.maps.co/) to geocode address into positions")
    st.write("Satellite basemaps from google and esri")
    st.write("streamlit and streamlit cloud solution for UI and hosting")

    st.write("[Code on GitHub](https://github.com/rupestre-campos/satellite-image-viewer)")
    return True

if __name__ == "__main__":
    main()