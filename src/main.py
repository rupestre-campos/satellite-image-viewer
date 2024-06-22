import streamlit as st
import streamlit_ext as ste

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

@st.cache_resource
def get_catalog_searcher():
    return CatalogSearcher(app_config_data.stac_url)

@st.cache_resource
def get_point_bufferer():
    return PointBufferer()

@st.cache_resource
def get_address_searcher():
    return AddressSearcher(
    api_url=app_config_data.geocoder_url,
    api_key=app_config_data.geocoder_api_key
)

@st.cache_resource
def get_image_renderer(rdn_block_size):
    return ImageRenderer(rdn_block_size=rdn_block_size)

@st.cache_resource
def get_animation_creator(_worker_catalog_searcher, _worker_image_renderer):
    return AnimationCreator(
    catalog_searcher=worker_catalog_searcher,
    image_renderer=worker_image_renderer
)

worker_catalog_searcher = get_catalog_searcher()
worker_point_bufferer = get_point_bufferer()
worker_address_searcher = get_address_searcher()
worker_image_renderer = get_image_renderer(app_config_data.rdn_block_size)
worker_animation_creator = get_animation_creator(worker_catalog_searcher, worker_image_renderer)

colormaps = sorted(worker_image_renderer.colormaps)


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
    coords,
    buffer_width,
    date_string,
    max_cloud_cover,
    satellite_params,
    time_per_image,
    period_time_break,
    width,
    view_params
    ):
    feature_geojson = {
        "type": "Feature",
        "properties": {},
        "geometry": buffer_point(
            coords[0],
            coords[1],
            buffer_width
        )
    }
    satellite_view_params = satellite_params.copy()
    if "assets" in satellite_view_params:
        satellite_view_params.pop("assets")
    if "expression" in satellite_view_params:
        satellite_view_params.pop("expression")
    if "RGB-expression" in satellite_view_params:
        satellite_view_params.pop("RGB-expression")
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
def catalog_search(max_items, coords, buffer_width, date_string, max_cloud_cover, collection, platforms):
    feature_geojson = {
        "type": "Feature",
        "properties": {},
        "geometry": buffer_point(
            coords[0],
            coords[1],
            buffer_width
        )
    }
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
    coords,
    buffer_width,
    satellite_params,
    view_params,
    image_range,
    color_formula,
    colormap,
    enhance_image,
    enhance_passes,
    compute_min_max,
    create_contour,
    contour_gap,
    max_size_pixels
    ):
    feature_geojson = {
        "type": "Feature",
        "properties": {},
        "geometry": buffer_point(
            coords[0],
            coords[1],
            buffer_width
        )
    }
    params = satellite_params.copy()
    params.update({
        "zip_file": True,
        "image_format": "PNG",
        "feature_geojson": feature_geojson,
        "stac_list": stac_list,
        "image_as_array": True,
        "enhance_image": enhance_image,
        "enhance_passes": enhance_passes,
        "compute_min_max": compute_min_max,
        "max_size": max_size_pixels
    })
    if "assets" in params:
        params.pop("assets")
    if "expression" in params:
        params.pop("expression")
    if "RGB-expression" in params:
        params.pop("RGB-expression")
    if create_contour:
        params.update({"create_contour": create_contour, "gap": contour_gap})
    params.update(view_params)
    params.update({"min_value":image_range[0], "max_value":image_range[1]})
    params.update({"color_formula": color_formula, "colormap":colormap})

    image_data = worker_image_renderer.render_mosaic_from_stac(params)

    return image_data

def create_download_zip_button(zip_file, name):
    zip_name = name[:128].replace(',','-')
    ste.download_button(
        label="Download Image data",
        data = zip_file,
        file_name = f"{zip_name}.zip",
        mime="application/octet-stream"
    )

def create_download_gif_button(gif_result):
    gif_name = f"result-{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    ste.download_button(
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
            "latitude": float(latitude),
            "longitude": float(longitude),
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
            "range":(
                satellite_sensor_params["index_min_value"],
                satellite_sensor_params["index_max_value"]
            ),
            "default": (
                satellite_sensor_params["index_min_value"],
                satellite_sensor_params["index_max_value"]
            ),
            "step":0.05
        }
    return {
        "range": (0.0, 63535.0),
        "default": (
            satellite_sensor_params["min_value"],
            satellite_sensor_params["max_value"]
        ),
        "step":1.0
    }

def get_default_view_options_index(view_mode, options):
    if view_mode == "assets":
        if app_config_data.default_composition_value_for_composite in options:
            return options.index(app_config_data.default_composition_value_for_composite)
        return 0
    if app_config_data.default_composition_value_for_index in options:
        return options.index(app_config_data.default_composition_value_for_index)
    return 0

def startup_session_variables():
    st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
    if "geometry" not in st.session_state:
        st.session_state["geometry"] = (0,0)
    if "user_draw" not in st.session_state:
        st.session_state["user_draw"] = {}
    if "where_to_go" not in st.session_state:
        st.session_state["where_to_go"] = ""
    if not "result_gif_image" in st.session_state:
        st.session_state["result_gif_image"] = {}

def create_options_menu(satellite_sensor_params):
    color_formula = ""
    colormap = ""
    view_modes = ["assets", "expression", "RGB-expression"]
    view_modes = [view_mode for view_mode in view_modes if view_mode in satellite_sensor_params]
    with st.expander("options"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            enhance_image = False
            if app_config_data.enable_enhance_image:
                enhance_image = ste.checkbox(
                    "enhance image resolution",
                    value=app_config_data.enhance_image_default,
                    key="enhance"
                )
                if enhance_image:
                    st.write(f"Buffer set to max {app_config_data.enhance_image_buffer_size}m")
            anti_aliasing = ste.checkbox(
                "anti-aliasing",
                value=app_config_data.default_anti_aliasing,
                key="anti-aliasing"
            )

            pixelate_image = not anti_aliasing
        with col2:
            enhance_passes = 0
            if enhance_image:
                enhance_passes_options = app_config_data.enhance_image_passes.split(",")
                enhance_passes_options_tag = [f"{4**int(value)}x" for value in enhance_passes_options]
                enhance_power = ste.radio(
                    "enhance power",
                    options=enhance_passes_options_tag,
                    index=0,
                    key="enhance-power"
                )

                enhance_passes = round(int(enhance_power.strip("x")) ** (1/4))
        with col3:
            buffer_width_config = float(app_config_data.buffer_width)
            if app_config_data.enable_buffer_control:
                buffer_width_config = ste.number_input(
                    "Buffer width (m)",
                    min_value=10,
                    max_value=app_config_data.buffer_max_width,
                    value=app_config_data.buffer_width,
                    key="buffer-width"
                )

            max_size_pixels = app_config_data.max_pixels_image
            if int(max_size_pixels) == 0:
                max_size_pixels = None
            if enhance_image:
                max_size_pixels = None
                if buffer_width_config > app_config_data.enhance_image_buffer_size:
                    buffer_width_config = app_config_data.enhance_image_buffer_size
                    st.query_params["buffer-width"] = buffer_width_config


        with col4:
            opacity = st.slider("image opacity", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
            max_stac_items = app_config_data.default_stac_items
            if app_config_data.enable_stac_items_control:
                max_stac_items = ste.number_input(
                    "Max images on mosaic",
                    min_value=1,
                    max_value=app_config_data.max_stac_items,
                    value=app_config_data.default_stac_items,
                    key="max-stac-items"
                )
            compute_min_max = True

            if satellite_sensor_params.get("collection_name")!="cop-dem-glo-30":
                compute_min_max = ste.checkbox(
                    "Compute min max from image", value=False, key="compute-min-max")

        if satellite_sensor_params.get("collection_name")=="cop-dem-glo-30" \
            and compute_min_max == False:
                st.query_params["compute-min-max"] = True
                compute_min_max = True


        #buffer_width = float(buffer_width_config)/(enhance_passes+1)
        buffer_width = buffer_width_config

        col1, col2 = st.columns(2)
        with col1:
            col3, col4 = st.columns(2)
            with col3:
                index = 0
                if len(view_modes) <= app_config_data.default_composition_index+1:
                    index = app_config_data.default_composition_index
                view_mode = ste.radio(
                    "Select image composition",
                    options=view_modes,
                    index=index,
                    key="img-comp"
                )
                if not view_mode:
                    view_mode = view_modes[app_config_data.default_composition_index]
                    st.query_params["img-comp"] = view_mode

            with col4:
                options = sorted(satellite_sensor_params[view_mode].keys())
                options_index = get_default_view_options_index(view_mode, options)
                selected_bands = ste.selectbox(
                    "Composition options",
                    options=options,
                    index=options_index,
                    key="img-view"
                )
                if not selected_bands:
                    selected_bands = options[options_index]
                    st.query_params["img-view"] = selected_bands

        with col2:
            min_max_range = get_min_max_image_range(view_mode, satellite_sensor_params)
            image_range_min = 0
            image_range_max = 1
            col3, col4 = st.columns(2)

            with col3:
                if not compute_min_max:
                    image_range_min = st.number_input(
                        "Image min value",
                        value=float(min_max_range["default"][0]),
                        min_value=min_max_range["range"][0],
                        max_value=min_max_range["range"][1],
                        step=float(0.1),
                        key="img-min"
                    )

            with col4:
                if not compute_min_max:
                    image_range_max = st.number_input(
                        "Image max value",
                        value=float(min_max_range["default"][1]),
                        min_value=min_max_range["range"][0],
                        max_value=min_max_range["range"][1],
                        step=float(0.1),
                        key="img-max"
                    )
                create_contour = False
                contour_gap = app_config_data.default_contour_equidistance
                if satellite_sensor_params.get("collection_name")=="cop-dem-glo-30" :
                    create_contour = True

                    contour_gap = ste.radio(
                        "contour equidistance (m)",
                        options=app_config_data.contour_equidistances,
                        index=app_config_data.contour_equidistances.index(app_config_data.default_contour_equidistance),
                        key="contour-gap"
                    )
                    if not contour_gap:
                        contour_gap = app_config_data.default_contour_equidistance
                    contour_gap = int(contour_gap)


            image_range = (image_range_min, image_range_max)
            view_param = {view_mode: satellite_sensor_params[view_mode][selected_bands]}

        if view_mode == "expression":
            col1, col2, col3, col4 = st.columns(4)
            with col2:
                colormap_disable = False
                if satellite_sensor_params.get("collection_name")=="cop-dem-glo-30" :
                    colormap_disable = True
                colormap = st.selectbox(
                    "Image colormap",
                    options=colormaps,
                    index=colormaps.index("viridis"),
                    key="colormap",
                    disabled=colormap_disable
                )
                if not colormap:
                    colormap = colormaps[colormaps.index("viridis")]

            return {
                "colormap": colormap,
                "color_formula": color_formula,
                "image_range": image_range,
                "view_param": view_param,
                "enhance_image": enhance_image,
                "enhance_passes": enhance_passes,
                "buffer_width": buffer_width,
                "compute_min_max": compute_min_max,
                "create_contour": create_contour,
                "contour_gap": contour_gap,
                "opacity": opacity,
                "max_stac_items": max_stac_items,
                "max_size_pixels": max_size_pixels,
                "pixelate_image": pixelate_image
            }

        col1, col2 = st.columns(2)
        with col1:
            col3, col4 = st.columns(2)
            with col3:
                gamma = ste.number_input(
                    "gamma",
                    value=satellite_sensor_params["color_formula_gamma"],
                    min_value=0.0,
                    max_value=app_config_data.max_gamma,
                    step=0.05,
                    key="img-gamma"
                )

            with col4:
                saturation = ste.number_input(
                    "saturation",
                    value=satellite_sensor_params["color_formula_saturation"],
                    min_value=0.0,
                    max_value=app_config_data.max_saturation,
                    step=0.05,
                    key="img-saturation"
                )
        with col2:
            col3, col4 = st.columns(2)
            with col3:
                sigmoidal = ste.number_input(
                    "sigmoidal",
                    value=satellite_sensor_params["color_formula_sigmoidal"],
                    min_value=0.0,
                    max_value=app_config_data.max_sigmoidal,
                    step=0.05,
                    key="img-sigmoidal"
                )
            with col4:
                sigmoidal_gain = ste.number_input(
                    "sigmoidal gain",
                    value=satellite_sensor_params["color_formula_sigmoidal_gain"],
                    min_value=0.0,
                    max_value=app_config_data.max_sigmoidal_gain,
                    step=0.05,
                    key="img-sigmoidal-gain"
                )

            color_formula = f"sigmoidal RGB {sigmoidal} {sigmoidal_gain} "\
                            f"gamma RGB {gamma} saturation {saturation}"
        return {
            "colormap": colormap,
            "color_formula": color_formula,
            "image_range": image_range,
            "view_param": view_param,
            "enhance_image": enhance_image,
            "enhance_passes": enhance_passes,
            "buffer_width": buffer_width,
            "compute_min_max": compute_min_max,
            "create_contour": create_contour,
            "contour_gap": contour_gap,
            "opacity": opacity,
            "max_stac_items": max_stac_items,
            "max_size_pixels": max_size_pixels,
            "pixelate_image": pixelate_image
        }

def create_gif_menu(
        date_string, satellite_sensor_params, max_cloud_percent, view_param, buffer_width):
    create_gif_button = False

    col1, col2, col3 = st.columns(3)
    with col1:
        time_per_image = ste.number_input(
            "Time per image (seconds)",
            min_value=app_config_data.gif_min_time_per_image,
            max_value=app_config_data.gif_max_time_per_image,
            step=0.01,
            value=app_config_data.gif_default_time_per_image,
            key="gif-time"
        )
    with col2:
        period_time_break = ste.number_input(
            "Interval between images (days)",
            min_value=app_config_data.gif_min_interval,
            max_value=app_config_data.gif_max_interval,
            value=app_config_data.gif_default_interval,
            key="gif-interval"
        )
    with col3:
        image_size = ste.number_input(
            "Output image size (pixels)",
            min_value=app_config_data.gif_min_img_size,
            max_value=app_config_data.gif_max_img_size,
            value=app_config_data.gif_default_img_size,
            key="gif-size"
        )

    create_gif_button = st.button("Render GIF")
    if create_gif_button:
        result_gif_image = create_gif(
            period_time_break=period_time_break,
            satellite_params=satellite_sensor_params,
            coords=st.session_state["geometry"],
            buffer_width=buffer_width,
            max_cloud_cover=max_cloud_percent,
            time_per_image=time_per_image,
            date_string=date_string,
            view_params=view_param,
            width=image_size,
        )
        st.session_state["result_gif_image"] = result_gif_image
        result_gif_image = None

def create_powered_by_menu():
    with st.expander("powered by:"):
        st.write("Satellites: ESA Sentinel 1,2 & NASA Landsat 4,5,6,8,9 hosted on S3 AWS")
        st.write("Earth Search STAC API from element84 to search images via pystac")
        st.write("rio_tiller to read and render STAC/COG links into a real image")
        st.write("streamlit-folium / folium / leaflet for the map")
        st.write("geocode.maps to geocode address into positions")
        st.write("Basemaps from Open Street Maps, Google and ESRI")
        st.write("streamlit and streamlit cloud solution for UI and hosting")
        st.write("pypi ISR for image enhancement")

    st.write("This application does not collect data but use carefully ;)")

def georreference_image_menu(image_bounds):
    colgeo_left, colgeo_center, colgeo_right = st.columns(3)
    with colgeo_left:
        empty = st.write("\t")
        delta_x_left = st.number_input(
            "< West",
            step=0.0005,
            min_value=-1.0,
            max_value=1.0,
            value=float(st.query_params.get("deltaxl",0.0)),
            key="deltaxl",
            format="%f")
    with colgeo_center:
        delta_y_up = st.number_input(
            "^ North",
            step=0.0005,
            min_value=-1.0,
            max_value=1.0,
            value=float(st.query_params.get("deltayu",0.0)),
            key="deltayu",
            format="%f")
        delta_y_down = st.number_input(
            "v South",
            step=0.0005,
            min_value=-1.0,
            max_value=1.0,
            value=float(st.query_params.get("deltayd",0.0)),
            key="deltayd",
            format="%f")
    with colgeo_right:
        empty = st.write("\t")
        delta_x_right = st.number_input(
            "East >",
            step=0.0005,
            min_value=-1.0,
            max_value=1.0,
            value=float(st.query_params.get("deltaxr",0.0)),
            key="deltaxr",
            format="%f")

    st.query_params["deltaxl"] = delta_x_left
    st.query_params["deltaxr"] = delta_x_right
    st.query_params["deltayu"] = delta_y_up
    st.query_params["deltayd"] = delta_y_down

    image_bounds = [
        [image_bounds[0][0]+delta_y_down, image_bounds[0][1]+delta_x_left],
        [image_bounds[1][0]+delta_y_up, image_bounds[1][1]+delta_x_right],
    ]
    return image_bounds

def get_web_map():
    web_map = WebMap()
    web_map.add_fullscreen()
    web_map.add_draw_support(
        polygon=app_config_data.enable_draw_polygon,
        retangle=app_config_data.enable_draw_retangle,
        marker=app_config_data.enable_draw_marker
    )
    web_map.add_mouse_location()
    web_map.add_base_map(app_config_data.google_basemap, "google satellite", "google", show=True)
    web_map.add_base_map(app_config_data.open_street_maps, "open street maps", "open street maps")
    web_map.add_base_map(app_config_data.esri_basemap, "esri satellite", "esri")
    return web_map

def main():
    startup_session_variables()
    web_map = get_web_map()

    st.title("Satellite Image Viewer")
    st.write("[Code on GitHub](https://github.com/rupestre-campos/satellite-image-viewer)")

    col1, col2 = st.columns(2)
    with col1:
        satellite_sensor = ste.radio(
            "Satellite",
            options=sorted(list(app_config_data.satelites.keys())),
            index=app_config_data.default_satellite_choice_index,
            key="satellite"
        )

    satellite_sensor_params = app_config_data.satelites.get(satellite_sensor)
    options_menu_values = create_options_menu(satellite_sensor_params)
    view_param = options_menu_values["view_param"]
    image_range = options_menu_values["image_range"]
    colormap = options_menu_values["colormap"]
    color_formula = options_menu_values["color_formula"]
    enhance_image = options_menu_values["enhance_image"]
    enhance_passes = options_menu_values["enhance_passes"]
    buffer_width = options_menu_values["buffer_width"]
    compute_min_max = options_menu_values["compute_min_max"]
    create_contour = options_menu_values["create_contour"]
    contour_gap = options_menu_values["contour_gap"]
    opacity = options_menu_values["opacity"]
    max_stac_items = options_menu_values["max_stac_items"]
    max_size_pixels = options_menu_values["max_size_pixels"]
    pixelate_image = options_menu_values["pixelate_image"
                                         ]
    start_date = datetime.strptime(
        satellite_sensor_params.get("start_date"),
        "%Y-%m-%d"
    )
    end_date = datetime.strptime(
        satellite_sensor_params.get("end_date"),
        "%Y-%m-%d"
    )

    col1, col2 = st.columns(2)

    with col1:
        search_place_type = ste.radio(
            "Searh type",
            options=["address", "coordinates"],
            key="search-type")
        if search_place_type == "address":
            pass
            #st.write("Enter address location")
        if search_place_type == "coordinates":
            st.write("Draw or Drop a pin on map")

    col1, col2 = st.columns(2)
    with col1:
        address_to_search = ""
        if search_place_type=="address":
            address_to_search = ste.text_input(
                "Search address, city, state or country",
                value=app_config_data.default_start_address,
                placeholder="John Doe st",
                key="address",
                max_chars=app_config_data.address_max_chars
            )

        if search_place_type=="coordinates":
            geom = st.session_state.get("geometry", (0.0, 0.0))

            latitude = round(
                float(st.query_params.get("lat", geom[0])),
                app_config_data.float_precision
            )
            longitude = round(
                float(st.query_params.get("lon", geom[1])),
                app_config_data.float_precision
            )
            st.session_state["geometry"] = (
                latitude,
                longitude
            )
            st.write(f"Lat/Long: {latitude}/{longitude}")
            st.query_params.update(
                {
                    "lat": latitude,
                    "lon": longitude,
                    "search-type": "coordinates"
                }
            )

    with col2:
        max_cloud_percent = 100
        disabled = False
        if satellite_sensor.lower() in ("sentinel 1", "copernicus dem"):
            disabled = True
        max_cloud_percent = st.number_input(
            "Maximum cloud cover (%)",
            min_value=0.0,
            max_value=100.0,
            value=app_config_data.default_cloud_cover,
            step=app_config_data.cloud_cover_step,
            key="cloud-perc",
            disabled=disabled
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.query_params.get("start-date"):
            query_param_date = st.query_params.get("start-date").replace("00:00:00", "").strip()
            if datetime.strptime(query_param_date, "%Y-%m-%d") < start_date:
                st.query_params["start-date"] = start_date
        if satellite_sensor.lower() not in ("copernicus dem"):
            start_date = ste.date_input(
                "Start date",
                value=start_date,
                min_value=start_date,
                max_value=end_date,
                format="YYYY-MM-DD",
                key="start-date"
            )
    with col2:
        if st.query_params.get("end-date"):
            query_param_date = st.query_params.get("end-date").replace("00:00:00", "").strip()
            if datetime.strptime(query_param_date, "%Y-%m-%d") > end_date:
                st.query_params["end-date"] = end_date
        if satellite_sensor.lower() not in ("copernicus dem"):
            end_date = ste.date_input(
                "End date",
                value=end_date,
                min_value=start_date,
                max_value=end_date,
                format="YYYY-MM-DD",
                key="end-date"
            )
        if end_date <= start_date:
            end_date = start_date + timedelta(days=1)

    selected_dates = (start_date, end_date)
    date_string = create_datestring_from_selected_dates(selected_dates)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if satellite_sensor_params["name"].lower() in app_config_data.allowed_gif_satellite:
            gif_check_box = ste.checkbox("GIF creator", value=False, key="gif-creator")
            if gif_check_box:
                create_gif_menu(
                    date_string, satellite_sensor_params, max_cloud_percent, view_param, buffer_width)
    with col2:
        georreference_image = ste.checkbox("Adjust image position", value=False, key="georref-img")

    warning_area_user_input_location = st.empty()
    warning_area_user_input = st.empty()

    if address_to_search != st.session_state["where_to_go"] \
        and search_place_type != "coordinates":
        st.session_state["where_to_go"] = address_to_search
        location = search_place(address_to_search)
        parsed_location = parse_location(location)
        if parsed_location["warning"]:
            warning_area_user_input_location.write(f":red[Location not found, try different keywords]")

        st.session_state["geometry"] = (
            round(parsed_location["latitude"], app_config_data.float_precision),
            round(parsed_location["longitude"], app_config_data.float_precision)
        )

        st.session_state["result_gif_image"] = {}
        st.rerun()

    stac_items = catalog_search(
        max_stac_items,
        st.session_state["geometry"],
        buffer_width,
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
            buffer_width,
            satellite_sensor_params,
            view_param,
            image_range,
            color_formula,
            colormap,
            enhance_image,
            enhance_passes,
            compute_min_max,
            create_contour,
            contour_gap,
            max_size_pixels
        )
        st.write(f'Image ID: {image_data["name"][:1024]}')
        with col1:
            create_download_zip_button(image_data["zip_file"], image_data["name"])

        image_bounds = image_data["bounds"]

        with col2:
            if georreference_image:
                image_bounds = georreference_image_menu(image_bounds)

        web_map.add_image(
            image_data["image"],
            image_bounds,
            satellite_sensor_params["name"],
            opacity
        )
        feature_geojson = {
            "type": "Feature",
            "properties": {},
            "geometry": buffer_point(
                st.session_state["geometry"][0],
                st.session_state["geometry"][1],
                buffer_width
            )
        }
        web_map.add_polygon(feature_geojson)
        if create_contour:
            web_map.add_contour(image_data["contours"])
        with col1:
            st.write(f"Min/Max values input: {image_data['min_value']:.2f}/{image_data['max_value']:.2f}")

    with col1:
        if st.session_state["result_gif_image"]:
            create_download_gif_button(st.session_state["result_gif_image"])

    web_map.add_layer_control()
    web_map.add_location_control()
    user_draw = web_map.render_web_map(pixelated=pixelate_image)
    create_powered_by_menu()
    if user_draw["geometry"] != None \
        and st.session_state["user_draw"] != user_draw["geometry"]:

        if user_draw.get("geometry", {}).get("type") == "Point":
            longitude = user_draw["geometry"]["coordinates"][0]
            latitude = user_draw["geometry"]["coordinates"][1]
            st.session_state["user_draw"] = user_draw["geometry"]
            st.session_state["geometry"] = (
                round(latitude, app_config_data.float_precision),
                round(longitude, app_config_data.float_precision)
            )

            st.session_state["result_gif_image"] = {}
            st.query_params.update({"lat": latitude, "lon":longitude, "search-type":"coordinates"})
            st.rerun()

    return True

if __name__ == "__main__":
    main()