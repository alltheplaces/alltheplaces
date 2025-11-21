from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaDESpider(Spider):
    name = "mazda_de"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    allowed_domains = ["www.mazda.de"]
    start_urls = None

    async def start(self) -> AsyncIterator[JsonRequest]:
        if self.start_urls:
            yield JsonRequest(url=self.start_urls[0])
        else:
            yield JsonRequest(url=f"https://{self.allowed_domains[0]}/api/dealers")

    def parse(self, response: Response) -> Iterable[Feature]:
        for feature_group in response.json()["data"]["dealers"]:
            if feature_group["active"] is not True:
                continue
            for feature in feature_group["services"]:
                if feature["isVisible"] is not True:
                    continue
                feature["contact"]["phoneNumber"] = feature["contact"]["phoneNumber"]["e164"]
                item = DictParser.parse(feature["contact"])
                item["branch"] = feature_group["name"]
                item.pop("name", None)
                match feature["name"]:
                    case "Car Sales":
                        apply_category(Categories.SHOP_CAR, item)
                        item["ref"] = feature_group["dealerCode"] + "_Sales"
                    case "Car Repair" | "Mazda Europe Service":
                        apply_category(Categories.SHOP_CAR_REPAIR, item)
                        item["ref"] = feature_group["dealerCode"] + "_Service"
                    case "Parts Sales":
                        apply_category(Categories.SHOP_CAR_PARTS, item)
                        item["ref"] = feature_group["dealerCode"] + "_Parts"
                    case (
                        "Online Leasing"
                        | "Online Service Booking"
                        | "Motability"
                        | "Mazda Your Way Service"
                        | "Approved Used-car Services"
                        | "Test Drive"
                        | "Courtesy car"
                        | "Collection & Delivery"
                    ):
                        continue
                    case _:
                        self.logger.error("Unknown dealer type: {}".format(feature["name"]))
                        continue
                item["opening_hours"] = OpeningHours()
                for day_hours in feature["openingTimes"]:
                    item["opening_hours"].add_range(day_hours["dayOfWeek"], day_hours["from"], day_hours["to"])
                item["extras"]["alt_ref"] = feature_group["dealerNumber"]
                yield from self.post_process_item(item, feature, feature_group)

    def post_process_item(self, item: Feature, feature: dict, feature_group: dict) -> Iterable[Feature]:
        if "Test & Training" in item["branch"]:
            return
        yield item
