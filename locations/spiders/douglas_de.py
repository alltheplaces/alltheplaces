from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT

DOUGLAS_SHARED_ATTRIBUTES = {"brand": "Douglas", "brand_wikidata": "Q2052213"}


class DouglasDESpider(JSONBlobSpider):
    name = "douglas_de"
    item_attributes = DOUGLAS_SHARED_ATTRIBUTES
    allowed_domains = ["www.douglas.de"]
    start_urls = ["https://www.douglas.de/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    locations_key = "stores"
    needs_json_request = True
    days = DAYS_DE
    user_agent = BROWSER_DEFAULT
    requires_proxy = True  # Data centre IP addresses appear to be blocked.

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))
        feature["id"] = feature.pop("name")
        feature["branch"] = feature.pop("displayName", None)
        feature["street_address"] = merge_address_lines([feature.pop("line1", None), feature.pop("line2", None)])
        if region_dict := feature.pop("region", None):
            feature["state"] = region_dict["isocodeShort"]
        feature["website"] = "https://{}{}".format(self.allowed_domains[0], feature.pop("url"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["branch"]
        item["opening_hours"] = OpeningHours()
        for day_hours in feature["openingHours"]["weekDayOpeningList"]:
            day_abbrev = self.days[day_hours["weekDayFull"].title()]
            if day_hours["closed"]:
                item["opening_hours"].set_closed(day_abbrev)
            else:
                item["opening_hours"].add_range(
                    day_abbrev, day_hours["openingTime"]["formattedHour"], day_hours["closingTime"]["formattedHour"]
                )
        apply_category(Categories.SHOP_PERFUMERY, item)
        yield item
