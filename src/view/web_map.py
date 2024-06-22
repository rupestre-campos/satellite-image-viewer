import folium
from folium.plugins import Draw, Fullscreen, MousePosition
from streamlit_folium import st_folium
from folium.plugins import LocateControl

class WebMap:
    def __init__(
            self,
            center_y=44.05,
            center_x=-121.42,
            zoom_start=12,
            zoom_control=True,
            min_zoom=6
        ):
        self.web_map = folium.Map(
            location=[center_y, center_x],
            zoom_start=zoom_start,
            zoom_control=zoom_control,
            max_bounds=True,
            min_zoom=min_zoom,
            control_scale=True,
            tiles = None
        )

    def add_fullscreen(self):
        Fullscreen(
            position="topleft",
        ).add_to(self.web_map)

    def add_mouse_location(self):
        MousePosition(
            position="bottomright",
        ).add_to(self.web_map)

    def add_layer_control(self):
        folium.LayerControl(
            collapsed=False
        ).add_to(self.web_map)

    def add_base_map(self, tile_url, name, attribution, max_zoom=30, max_native_zoom=18, show=False):
        folium.raster_layers.TileLayer(
            name=name,
            tiles=tile_url,
            attr=attribution,
            max_zoom=max_zoom,
            max_native_zoom=max_native_zoom,
            show=show,
            overlay=False
        ).add_to(self.web_map)

    def add_draw_support(self, polygon=True, retangle=True, marker=True, export=False):
        Draw(
            export=export,
            position="topleft",
            draw_options={
                "polyline": False,
                "polygon": polygon,
                "rectangle": retangle,
                "circle": False,
                "marker": marker,
                "circlemarker": False
            },
            edit_options={
                "edit": False,
                "remove": False,
            }
        ).add_to(self.web_map)

    def _streamlit_render(self, pixelated):
        return st_folium(
            self.web_map,
            use_container_width=True,
            pixelated=pixelated,
            returned_objects=["all_drawings"],
        )

    def render_web_map(self, pixelated=True):
        user_data = self._streamlit_render(pixelated)
        if not user_data["all_drawings"]:
            return {"geometry":None}
        return {"geometry": user_data["all_drawings"][0]["geometry"]}

    def add_image(self, image, image_bounds, name="satelite image", opacity=100):

        image_overlay = folium.raster_layers.ImageOverlay(
            image=image,
            name=name,
            opacity=opacity,
            bounds=image_bounds,

        )
        image_overlay.add_to(self.web_map)

        self.web_map.fit_bounds(
            self.web_map.get_bounds(), padding=(30, 30))

    def add_polygon(self, geojson_polygon):
        polygon = folium.GeoJson(
            geojson_polygon,
            name="Polygon",
            show=True,
            style_function=lambda feature: {
                "fillColor": None,
                "fill":None,
                "color": "black",
                "weight": 2,
        },
        )
        polygon.add_to(self.web_map)

    @staticmethod
    def contour_style_function(feature):
        pixel_value = feature.get("properties", {}).get("pixel_value", 5)
        if str(int(pixel_value))[-1] == "0":
            return {
                "color": "orange",
                "opacity": 0.8,
                "weight": 1.2
            }
        return {
                "color": "darkorange",
                "dashArray" : "3, 6",
                "opacity": 0.6,
                "weight": 0.9

            }

    def add_contour(self, geojson_contour):
        tooltip = folium.GeoJsonTooltip(
            fields=["pixel_value"],
            aliases=["Altitude (m) :"],
        )
        popup = folium.GeoJsonPopup(
            fields=["pixel_value"],
            aliases=["Altitude (m) :"],
        )
        highlight_function = lambda x: {
            "color": "red",
            "opacity": 0.8,
            "weight": 2.3
        }

        contour = folium.GeoJson(
            geojson_contour,
            name="Contour",
            show=False,
            marker=folium.Marker(
                icon=folium.Icon(
                    icon="plus",
                    angle=45,
                    color="black",
                    icon_color="orange",
                    **{"iconSize":[0,0], "iconAnchor":[10,20], "popupAnchor":[0,0], "shadowSize":[0,0]})),
            style_function=lambda x: self.contour_style_function(x),
            tooltip=tooltip,
            popup=popup,
            popup_keep_highlighted=True,
            highlight_function=highlight_function
        )

        contour.add_to(self.web_map)


    def add_location_control(self):
        LocateControl(auto_start=False, position="topright").add_to(self.web_map)