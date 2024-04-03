import pyproj
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from shapely.geometry import shape
from shapely.ops import transform


class BufferPoint:
    def __init__(self, geographic_crs="EPSG:4326", projected_crs="EPSG:3857"):
        self.geographic_crs = pyproj.CRS(geographic_crs)
        self.projected_crs = pyproj.CRS(projected_crs)
        self.transform_geo_to_projected = self.__get_geo_transform(geographic_crs, projected_crs)
        self.transform_project_to_geo = self.__get_geo_transform(projected_crs, geographic_crs)

    @staticmethod
    def __get_geo_transform(origin_crs, destination_crs):
        return pyproj.Transformer.from_crs(origin_crs, destination_crs, always_xy=True).transform

    @staticmethod
    def __buffer_point(point, buffer_distance):
        return point.buffer(buffer_distance)

    @staticmethod
    def __parse_lat_long_as_point(latitude, longitude):
        return Point(longitude, latitude)

    @staticmethod
    def __geometry_as_geojson(input_geom):
        return input_geom.__geo_interface__

    def __transform_to_meters(self, input_geom):
        return transform(self.transform_geo_to_projected, input_geom)

    def __transform_to_geo(self, input_geom):
        return transform(self.transform_project_to_geo, input_geom)

    def __lat_long_to_point_meters(self, latitude, longitude):
        input_point = self.__parse_lat_long_as_point(latitude, longitude)
        return self.__transform_to_meters(input_point)

    def __buffer_to_geojson(self, polygon):
        polygon = self.__transform_to_geo(polygon)
        return self.__geometry_as_geojson(Polygon(polygon))

    def buffer(self, latitude, longitude, buffer_distance=100):
        input_point = self.__lat_long_to_point_meters(latitude, longitude)
        buffered_point = self.__buffer_point(input_point, buffer_distance)
        return self.__buffer_to_geojson(buffered_point)
