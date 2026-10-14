import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AmatosSpider(WPStoreLocatorSpider):
    name = "amatos"
    item_attributes = {"brand": "Amato's", "brand_wikidata": "Q4740614"}
    start_urls = [
        "https://www.amatos.com/wp-admin/admin-ajax.php?action=store_search&autoload=1&lat=43.6541625&lng=-70.2802368"
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["email"] = None
        branch = re.sub(r"^Amato\S*\s*[–@-]?\s*", "", item.pop("name"))
        item["branch"] = re.sub(r",\s*(?:[A-Z]{2}|Maine)\b.*$", "", branch).strip()
        item["street_address"] = re.sub(r",?\s*\((?:@|in)\s[^)]*\)", "", item["street_address"]).strip()
        item["website"] = feature.get("permalink")
        apply_category(Categories.FAST_FOOD, item)
        yield item

    def parse_opening_hours(self, feature: dict, days: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, ranges in re.findall(r's:\d+:"(\w+)";a:\d+:\{(.*?)\}', feature.get("wpsl_hours") or ""):
            for open_time, close_time in re.findall(r's:\d+:"([^",]+),([^"]+)"', ranges):
                oh.add_range(days[day.title()], open_time, close_time, "%I:%M %p")
        return oh
