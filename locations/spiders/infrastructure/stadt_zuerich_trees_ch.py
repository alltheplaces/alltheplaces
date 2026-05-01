from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses


class StadtZuerichTreesCHSpider(Spider):
    name = "stadt_zuerich_trees_ch"
    allowed_domains = ["www.ogd.stadt-zuerich.ch"]
    dataset_attributes = Licenses.CC0.value
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    start_urls = [
        "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Baumkataster?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON&typename=baumkataster_baumstandorte"
    ]

    def parse(self, response):
        for f in response.json()["features"]:
            props = f.get("properties", {})
            extras = {}
            if diameter := props.get("kronendurchmesser"):
                extras["diameter"] = f"{diameter} m"
            if genus := props.get("baumgattunglat"):
                extras["genus"] = genus
            if species := props.get("baumnamelat"):
                extras["species"] = species
            if year := props.get("pflanzjahr"):
                extras["start_date"] = str(year)
            feature = Feature(
                ref=props["poi_id"],
                lat=f["geometry"]["coordinates"][1],
                lon=f["geometry"]["coordinates"][0],
                city="Zürich",
                country="CH",
                extras=extras,
            )
            apply_category(Categories.NATURAL_TREE, feature)
            yield feature
