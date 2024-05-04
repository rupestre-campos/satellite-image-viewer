from controller.catalog_searcher import CatalogSearcher
from controller.image_renderer import ImageRenderer

from datetime import datetime
from datetime import timedelta
import io
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


class AnimationCreator:
    def __init__(self, catalog_searcher, image_renderer):
        self.catalog_searcher = catalog_searcher
        self.image_renderer = image_renderer

    @staticmethod
    def __format_datetime(datetime_obj):
        return datetime_obj.strftime("%Y-%m-%d")

    @staticmethod
    def __parse_date_string(date_string):
        dates = date_string.split("/")
        start_date = datetime.strptime(dates[0], "%Y-%m-%d")
        end_date = datetime.strptime(dates[1], "%Y-%m-%d")
        return (start_date, end_date)

    def __subidivide_time_range(self, date_string, each_days=90):
        date_ranges = []
        parsed_date = self.__parse_date_string(date_string)
        start_date = parsed_date[0]
        end_date = parsed_date[1]
        interval = timedelta(days=each_days)
        date_range_start = start_date
        while date_range_start < end_date:
            date_range_end = min(date_range_start + interval, end_date)
            start_date_format = self.__format_datetime(date_range_start)
            end_date_format = self.__format_datetime(date_range_end)
            date_ranges.append(f"{start_date_format}/{end_date_format}")
            date_range_start = date_range_end
        return date_ranges

    @staticmethod
    def __parse_image(image):
        image = io.BytesIO(image)
        return Image.open(image)

    @staticmethod
    def __save_gif(image_list, time_per_image_seconds=1):
        with io.BytesIO() as buffer:
            image_list[0].save(
                fp=buffer,
                format="GIF",
                append_images=image_list[1:],
                save_all=True,
                duration=time_per_image_seconds*1000,
                loop=0
            )
            buffer.seek(0)
            return buffer.getvalue()

    @staticmethod
    def __burn_date_into_image(image, text, text_font, font_size, width, height):
        draw = ImageDraw.Draw(image)
        draw.text(
            (width/2, height*0.08),
            text,
            fill=(0,0,0,255),
            anchor="mt",
            font=text_font,
            stroke_width=int(font_size*0.06),
            stroke_fill=(255,255,255,255)
            )
        return image

    @staticmethod
    def __get_text_font(font_size):
        return ImageFont.load_default(size=font_size)

    @staticmethod
    def __resize_image(image, width, height):
        return image.resize((width,height), Image.BILINEAR)

    def create_gif(self, params):
        feature_geojson = params.pop("feature_geojson", {})
        date_string = params.get("date_string")
        period_time_break = params.get("period_time_break", 90)
        image_search_params = params.get("image_search")
        image_render_params = params.get("image_render")
        font_size = params.get("font_size", 0.08)
        width = params.get("width", 300)
        height = params.get("height", 300)
        font_size = height*font_size
        text_font = self.__get_text_font(
            font_size
        )
        date_ranges = self.__subidivide_time_range(date_string, each_days=period_time_break)
        image_search_params.update({"feature_geojson": feature_geojson})
        image_render_params.update({"feature_geojson": feature_geojson})
        images = []
        for date_range in date_ranges:
            end_date = date_range.split("/")[-1]
            image_search_params.update({"date_string": date_range})
            stac_items = self.catalog_searcher.search_images(image_search_params)
            if len(stac_items)==0:
                continue
            image_render_params.update({"stac_list": stac_items, "image_format": "PNG"})

            result_image = self.image_renderer.render_mosaic_from_stac(image_render_params)

            image = self.__parse_image(result_image.pop("image"))
            image = self.__resize_image(image, width, height)
            image = self.__burn_date_into_image(
                image, end_date, text_font, font_size, width, height)
            images.append(image)

        if len(images) == 0:
            raise ValueError("No image found")

        image_gif = self.__save_gif(images, time_per_image_seconds=params.get("time_per_image", 1))
        return {
            "image": image_gif,
            "projection_file": result_image.get("projection_file"),
            "bounds": result_image.get("bounds")
        }
