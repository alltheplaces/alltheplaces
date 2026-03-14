import csv
from io import StringIO
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

TEXACO_SHARED_ATTRIBUTES = {"brand": "Texaco", "brand_wikidata": "Q775060"}


class TexacoCOSpider(Spider):
    name = "texaco_co"
    item_attributes = TEXACO_SHARED_ATTRIBUTES
    start_urls = [
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vSUovHjq-9eCVzmq-0Ms-vilXmqjokKGz23lGG4xq2AsyJEbiXbBfyI3XUMiexm7OctFPmgIUSgGHni/pub?gid=273428871&single=true&output=csv"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        reader = csv.DictReader(StringIO(response.text))
        seen_coords = set()
        for row in reader:
            if row.get("brand") != "TEXACO":
                continue
            lat = row.get("geolocation.latitude")
            lon = row.get("geolocation.longitude")
            if not lat or not lon:
                continue
            coords = (lat, lon)
            if coords in seen_coords:
                continue
            seen_coords.add(coords)
            item = Feature(
                name=row.get("station_name"),
                street_address=row.get("address"),
                city=row.get("city"),
                state=row.get("province"),
                lat=lat,
                lon=lon,
            )
            apply_category(Categories.FUEL_STATION, item)
            yield item
