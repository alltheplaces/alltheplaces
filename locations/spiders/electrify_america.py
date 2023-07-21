import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ElectrifyAmericaSpider(scrapy.Spider):
    name = "electrify_america"
    item_attributes = {"brand": "Electrify America", "brand_wikidata": "Q59773555"}
    start_urls = ["https://api-prod.electrifyamerica.com/v2/locations"]

    def parse(self, response):
        for item in response.json():
            feature = DictParser.parse(item)
            apply_category(Categories.CHARGING_STATION, feature)
            feature["street_address"] = feature.pop("addr_full")

            extras = dict()
            extras["capacity"] = item.get("evseMax")

            if access := item.get("type"):
                if access == "PUBLIC":
                    extras["access"] = "public"

            if "extras" not in feature:
                feature["extras"] = dict()
            feature["extras"].update(extras)

            yield feature
