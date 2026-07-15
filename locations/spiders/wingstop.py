import json
import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no, map_payment
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import clean_facebook


class WingstopSpider(SitemapSpider):
    name = "wingstop"
    item_attributes = {"brand": "Wingstop", "brand_wikidata": "Q8025339"}
    sitemap_urls = ["https://locations.wingstop.com/sitemap.xml"]
    sitemap_rules = [(r"/wingstop-[^/]+/classic-wings$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        location = json.loads(
            unquote(
                re.search(
                    r"JSON\.parse\(decodeURIComponent\(\"(.+)\"\)\)",
                    response.xpath('//script[@type="module"]/text()').get(),
                ).group(1)
            )
        )["document"]

        item = DictParser.parse(location)
        item["ref"] = location["c_internalStoreCode"]
        item["website"] = location["websiteUrl"]["url"]
        if restaurant_name := location.get("c_oloRestaurantName"):
            item["branch"] = restaurant_name.removeprefix("Wingstop").strip()
        if facebook_page_url := location.get("facebookPageUrl"):
            item["facebook"] = clean_facebook(facebook_page_url)

        for payment_option in location.get("paymentOptions") or []:
            map_payment(item, payment_option, PaymentMethods)

        item["opening_hours"] = self.parse_hours(location.get("hours") or {})

        apply_yes_no(Extras.DELIVERY, item, location.get("olo_supportsDispatch") == "true")
        apply_yes_no(Extras.DRIVE_THROUGH, item, location.get("olo_supportsDrivethru") == "true")
        apply_yes_no(Extras.TAKEAWAY, item, "In-Store Pickup" in (location.get("pickupAndDeliveryServices") or []))

        apply_category(Categories.FAST_FOOD, item)

        yield item

    def parse_hours(self, hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            rule = hours.get(day)
            if not isinstance(rule, dict):
                continue
            if rule.get("isClosed") is True:
                oh.set_closed(day)
                continue
            for interval in rule.get("openIntervals") or []:
                oh.add_range(day, interval["start"], interval["end"])
        return oh
