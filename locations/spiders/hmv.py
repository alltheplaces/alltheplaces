import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class HmvSpider(JSONBlobSpider):
    name = "hmv"
    item_attributes = {"brand": "HMV", "brand_wikidata": "Q10854572"}
    start_urls = ["https://hmv.com/api/stores?limitTo=3000&source=StoreFinder&type=1&postcode=Birmingham"]
    locations_key = ["stores"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    needs_json_request = True

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([feature["addressOne"], feature["addressTwo"]])
        #        item["instagram"] = feature["Instagram"]
        item["branch"] = item.pop("name").replace("hmv ", "")
        item["twitter"] = feature["twitter"]

        try:
            item["opening_hours"] = self.parse_opening_hours(feature["openingTimes"])
        except:
            pass

        apply_category(Categories.SHOP_MUSIC, item)

        yield item

    def parse_opening_hours(self, opening_times: str) -> OpeningHours:
        oh = OpeningHours()
        for day, time in re.findall(r"(?:<br>|<strong>)(.+?):(?:|</strong>)?<span>(.+?)</span>", opening_times):
            if time == "Closed":
                oh.set_closed(day)
            else:
                oh.add_range(day, *time.split(" - "))
        return oh
