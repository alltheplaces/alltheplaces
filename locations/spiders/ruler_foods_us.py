import re

from locations.hours import DAYS, OpeningHours
from locations.storefinders.store_locator_plus_self import StoreLocatorPlusSelfSpider
from locations.structured_data_spider import clean_facebook


class RulerFoodsUSSpider(StoreLocatorPlusSelfSpider):
    name = "ruler_foods_us"
    item_attributes = {"brand": "Ruler Foods", "brand_wikidata": "Q17125470"}
    allowed_domains = ["rulerfoods.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 500
    max_results = 50

    def parse_item(self, item, location):
        item.pop("website", None)
        item["facebook"] = clean_facebook(location.get("url"))
        hours_range = re.sub(r"\s+", " ", location["hours"]).strip().upper()
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_days_range(DAYS, *hours_range.split(" TO ", 1), "%I:%M %p")
        yield item
