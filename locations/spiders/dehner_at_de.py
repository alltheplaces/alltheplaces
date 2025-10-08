from typing import Iterable

from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DehnerATDESpider(JSONBlobSpider):
    name = "dehner_at_de"
    item_attributes = {"brand": "Dehner", "brand_wikidata": "Q1183029"}
    start_urls = ["https://www.dehner.at/merchant-list/", "https://www.dehner.de/merchant-list/"]
    locations_key = "data"

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.pop("id_merchant")
        feature["address"]["housenumber"] = feature["address"].pop("number")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = response.urljoin(item["website"])
        oh = OpeningHours()
        for day_line in feature["opening_hours"]:
            oh.add_range(day_line["weekDayKey"], day_line["timeFrom"], day_line["timeTo"], time_format="%H:%M:%S.%f")
        item["opening_hours"] = oh
        yield item
