import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class HmvGBSpider(JSONBlobSpider):
    name = "hmv_gb"
    item_attributes = {"brand": "HMV", "brand_wikidata": "Q10854572"}
    start_urls = ["https://hmv.com/api/stores?limitTo=3000&source=StoreFinder&type=1&postcode=Birmingham"]
    locations_key = ["stores"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    needs_json_request = True

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([feature["addressOne"], feature["addressTwo"]])
        #        item["instagram"] = feature["Instagram"]
        item["opening_hours"] = OpeningHours()
        for day, time in re.findall(
            r"(?:<br>|<strong>)(.+?):(?:|</strong>)?<span>(.+?)</span>", feature["openingTimes"]
        ):
            if time == "Closed":
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_range(day, *time.split(" - "))
        item["branch"] = item.pop("name").replace("hmv ", "")
        item["twitter"] = feature["twitter"]

        apply_category(Categories.SHOP_MUSIC, item)

        yield item
