import folium
from folium.plugins import Draw
from streamlit_folium import st_folium

class WebMap:
    def __init__(self, center_y=-21, center_x=-45, zoom_start=12, zoom_control=False):
        self.web_map = folium.Map(
            location=[center_y, center_x],
            zoom_start=zoom_start,
            zoom_control=zoom_control
        )

    def add_draw_support(self, export=False):
        Draw(
            export=export,
            position="topleft",
            draw_options={
                "polyline": False,
                "polygon": False,
                "circle": False,
                "marker": False,
                "circlemarker": False
            },
            edit_options={
                "edit": False,
                "remove": False,
            }
        ).add_to(self.web_map)

    def _streamlit_render(self):
        return st_folium(self.web_map, use_container_width=True)

    def render_web_map(self):
        user_data = self._streamlit_render()
        if not user_data["last_active_drawing"]:
            return {"geometry":None}
        return {"geometry": user_data["last_active_drawing"]["geometry"]}

    def add_image(self, image, image_bounds):

        image_overlay = folium.raster_layers.ImageOverlay(
            image=image.data,
            name='satelite image',
            opacity=1,
            bounds=image_bounds,
        )
        image_overlay.add_to(self.web_map)
        self.web_map.fit_bounds(
            self.web_map.get_bounds(), padding=(30, 30))

    def add_polygon(self, geojson_polygon):
        polygon = folium.GeoJson(
            geojson_polygon,
            style_function=lambda feature: {
                "fillColor": None,
                "fill":None,
                "color": "orange",
                "weight": 2,
        },
        )
        polygon.add_to(self.web_map)