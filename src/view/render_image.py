from rio_tiler.io import STACReader
from rasterio import warp

def geojson_geometry_to_feature(geojson_geometry):
    return {
        "type": "Feature",
        "properties": {},
        "geometry": geojson_geometry
    }

def get_image_bounds(image):
    dest_crs = "EPSG:4326"
    left, bottom, right, top = [i for i in image.bounds]
    bounds_4326 = warp.transform_bounds(
        src_crs=image.crs, dst_crs=dest_crs, left=left,
        bottom=bottom, right=right, top=top)

    return [[bounds_4326[1], bounds_4326[0]], [bounds_4326[3], bounds_4326[2]]]

def render_image_from_stac(stac_item, geojson_geometry):
    with STACReader(None, item=stac_item) as stac:
        image = stac.feature(
            geojson_geometry_to_feature(geojson_geometry),
            assets=("red", "green", "blue",),
        )

    image_bounds = get_image_bounds(image)
    image = image.data_as_image()
    return image, image_bounds
