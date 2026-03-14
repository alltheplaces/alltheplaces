from typing import Iterable

from requests import Response
from scrapy import Selector

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CleverFitSpider(JSONBlobSpider):
    name = "clever_fit"
    item_attributes = {"brand": "Clever fit", "brand_wikidata": "Q27909675"}
    start_urls = ["https://www.clever-fit.com/wp-json/clever/studios"]

    def pre_process_data(self, feature: dict) -> None:
        for key in list(feature.keys()):
            if key.startswith("studio"):
                feature[key.removeprefix("studio")] = feature.pop(key)
        feature["branch"] = feature.pop("Name")
        feature["name"] = "Clever fit"
        feature["longitude"] = feature["address"].get("longitude")
        feature["latitude"] = feature["address"].get("latitude")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["branch"]
        if "openingHours" in feature:
            try:
                oh = OpeningHours()
                for day_hours in feature["openingHours"]:
                    oh.add_range(day_hours["dayOfWeek"], day_hours["timeFrom"], day_hours["timeTo"])
                item["opening_hours"] = oh
            except TypeError:
                # Some feature["openingHours"] are just a boolean
                pass
        social_media = Selector(text=feature["socialMediaHtml"])
        for link in social_media.xpath("//a/@href").getall():
            if "facebook" in link:
                item["facebook"] = link
            if "instagram" in link:
                item["extras"]["instagram"] = link
        yield item
