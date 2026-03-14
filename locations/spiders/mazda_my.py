from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaMYSpider(JSONBlobSpider):
    name = "mazda_my"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    allowed_domains = ["mazda.com.my"]
    start_urls = ["https://mazda.com.my/vehicleinfoapi/contentapi/dealerapi"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        item["branch"] = item.pop("name", None)
        item["addr_full"] = merge_address_lines([feature["addressOne"], feature["addressTwo"]])
        if item["email"]:
            item["email"] = item["email"].split()[0]
        item["opening_hours"] = OpeningHours()
        hours_text = " ".join(Selector(text=feature["hours"]).xpath("//text()").getall()).replace(
            "Sunday & Public Holiday", "Sunday"
        )
        item["opening_hours"].add_ranges_from_string(hours_text)
        match feature["type"]:
            case "Sales":
                apply_category(Categories.SHOP_CAR, item)
            case "Service" | "Body & Paint":
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            case "Parts":
                apply_category(Categories.SHOP_CAR_PARTS, item)
            case _:
                self.logger.error("Unknown location type: {}".format(feature["type"]))
        yield item
