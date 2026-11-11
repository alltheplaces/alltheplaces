import json
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class KmartAUSpider(SitemapSpider):
    name = "kmart_au"
    item_attributes = {"brand": "Kmart", "brand_wikidata": "Q6421682", "country": "AU"}
    allowed_domains = ["kmart.com.au"]
    sitemap_urls = ["https://www.kmart.com.au/sitemap/au/storelocation-sitemap.xml"]
    sitemap_rules = [("/store-detail/", "parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: TextResponse, **kwargs) -> Iterable[Feature]:
        # Store pages only include JSON-LD for some stores (it is missing for e.g. 24 hour stores), but the
        # Next.js page data always has the location
        next_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get("{}"))
        location = next_data.get("props", {}).get("pageProps", {}).get("location")
        if not location:
            return

        if location.get("state") in ("North Island", "South Island"):
            # The sitemap includes the odd New Zealand store
            return

        public_name = (location.get("publicName") or "").strip()
        item = DictParser.parse(location)
        item["branch"] = public_name.replace("K Hub", "").strip()
        item["name"] = "K Hub" if "K Hub" in public_name else "Kmart"
        item["street_address"] = merge_address_lines(
            [location.get("address1"), location.get("address2"), location.get("address3")]
        )
        item["website"] = response.url
        item["opening_hours"] = self.parse_hours(location.get("tradingHours") or [])

        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item

    @staticmethod
    def parse_hours(trading_hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in trading_hours:
            if day := sanitise_day(rule.get("weekDay", "")):
                hours = (rule.get("hours") or "").strip()
                if hours.lower() == "24hr":
                    oh.add_range(day, "00:00", "24:00")
                elif hours.lower() == "closed":
                    oh.set_closed(day)
                elif "-" in hours:
                    open_time, close_time = hours.split("-", 1)
                    oh.add_range(day, open_time.strip(), close_time.strip(), "%I:%M%p")
        return oh
