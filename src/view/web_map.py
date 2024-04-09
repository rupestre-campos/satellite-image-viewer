import folium
from folium.plugins import Draw
from streamlit_folium import st_folium

class WebMap:
    def __init__(self, center_y=44.05, center_x=-121.42, zoom_start=12, zoom_control=False, min_zoom=3):
        self.web_map = folium.Map(
            location=[center_y, center_x],
            zoom_start=zoom_start,
            zoom_control=zoom_control,
            max_bounds=True,
            min_zoom=min_zoom,
            control_scale=True,
            tiles = None
        )

    def add_layer_control(self):
        folium.LayerControl().add_to(self.web_map)

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

    def add_draw_support(self, export=False):
        Draw(
            export=export,
            position="topleft",
            draw_options={
                "polyline": False,
                "polygon": False,
                "rectangle": False,
                "circle": False,
                "marker": True,
                "circlemarker": False
            },
            edit_options={
                "edit": False,
                "remove": False,
            }
        ).add_to(self.web_map)

    def _streamlit_render(self, pixelated):
        return st_folium(self.web_map, use_container_width=True, pixelated=pixelated)

    def render_web_map(self, pixelated=True):
        user_data = self._streamlit_render(pixelated)
        if not user_data["last_active_drawing"]:
            return {"geometry":None}
        return {"geometry": user_data["last_active_drawing"]["geometry"]}

    def add_image(self, image, image_bounds, name='satelite image'):

        image_overlay = folium.raster_layers.ImageOverlay(
            image=image,
            name=name,
            opacity=1,
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
                "color": "orange",
                "weight": 2,
        },
        )
        polygon.add_to(self.web_map)