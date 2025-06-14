from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FI, DAYS_NO, DAYS_PL, DAYS_SE, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KappahlSpider(JSONBlobSpider):
    name = "kappahl"
    item_attributes = {"brand": "KappAhl", "brand_wikidata": "Q4349016"}
    start_urls = [
        "https://www.kappahl.com/fi-fi/kaupat/search",
        "https://www.kappahl.com/nb-no/butikker/search",
        "https://www.kappahl.com/pl-pl/sklepy/search",
        "https://www.kappahl.com/sv-se/butiker/search",
    ]
    COUNTRY_DAYS_MAP = {
        "FIN": DAYS_FI,
        "NOR": DAYS_NO,
        "POL": DAYS_PL,
        "SWE": DAYS_SE,
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def pre_process_data(self, feature: dict) -> None:
        feature.update({key: value["$c"] for key, value in feature.pop("content").items()})

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = response.urljoin(feature.get("url"))
        item["opening_hours"] = OpeningHours()
        country_days = self.COUNTRY_DAYS_MAP.get(feature["country"])
        for rule in feature.get("openingHours", []):
            start_day = sanitise_day(rule.get("fromDay"), country_days)
            end_day = sanitise_day(rule.get("toDay"), country_days)
            if start_day and end_day:
                days_range = day_range(start_day, end_day)
                if rule.get("isClosed"):
                    item["opening_hours"].set_closed(days_range)
                else:
                    item["opening_hours"].add_days_range(days_range, rule.get("openFrom"), rule.get("openUntil"))
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
