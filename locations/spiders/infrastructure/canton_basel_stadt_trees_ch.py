from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses


class CantonBaselStadtTreesCHSpider(Spider):
    name = "canton_basel_stadt_trees_ch"
    allowed_domains = ["www.ogd.stadt-zuerich.ch"]
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "Canton of Basel-Stadt",
        "attribution:website": "https://data.bs.ch/",
        "attribution:wikidata": "Q12172",
        "contact:email": "opendata@bs.ch",
        "name:de": "Baumkataster",
        "use:openstreetmap": "yes",  # https://data-bs.ch/stata/dataspot/permalinks/20240822-osm-vektordaten.pdf
        "website": "https://data.bs.ch/explore/dataset/100052/information/",
    }
    custom_settings = {"DOWNLOAD_TIMEOUT": 90}
    start_urls = [
        "https://data.bs.ch/api/explore/v2.1/catalog/datasets/100052/exports/geojson",
    ]

    def parse(self, response: JsonResponse) -> Iterable[Feature]:
        for f in response.json()["features"]:
            lon, lat = f["geometry"]["coordinates"][:2]
            props = f["properties"]
            extras = {}
            if species := props.get("baumart_lateinisch"):
                species = species.replace(" x ", " × ").strip()
                genus = species.split()[0]
                if species != genus:
                    extras["species"] = species
                extras["genus"] = genus
            if start_date := props.get("timeposition"):
                extras["start_date"] = start_date
            feature = Feature(
                lat=round(lat, 7),
                lon=round(lon, 7),
                ref=props.get("ba_baumnr"),
                city=props.get("ba_gemeinde"),
                street=props.get("ba_strasse"),
                country="CH",
                extras=extras,
            )
            apply_category(Categories.NATURAL_TREE, feature)
            yield feature
