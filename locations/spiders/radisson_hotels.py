from typing import Any, Iterable

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class RadissonHotelsSpider(scrapy.Spider):
    name = "radisson_hotels"
    allowed_domains = ["www.radissonhotels.com"]
    brand_mapping = {
        "rdb": ["Radisson Blu", "Q7281341"],
        "rco": ["Radisson Collection", "Q60716706"],
        "pii": ["Park Inn by Radisson", "Q60711675"],
        "rdr": ["Radisson RED", "Q28233721"],
        "cis": ["Country Inn & Suites by Radisson", "Q5177332"],
        "pph": ["Park Plaza Hotels & Resorts", "Q2052550"],
        "art": ["Art’otel", "Q14516231"],
        "rad": ["Radisson", "Q1751979"],
        # I did not find the sub-brand wikidata so I put None.
        "prz": ["Prizeotel", None],
        "rdi": ["Radisson Individuals", None],
        "ri": ["Radisson Individuals", None],
    }
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_TIMEOUT": 300,
    }

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.radissonhotels.com/zimba-api/hotels?limit=1000", headers={"accept-language": "en-us"}
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for hotel in response.json()["hotels"]:
            hotel.update(hotel.pop("contactInfo"))
            item = DictParser.parse(hotel)
            item["ref"] = hotel.get("code")
            item["street_address"] = item.pop("addr_full")
            for page in hotel.get("pages", []):
                if page.get("code") == "overview":
                    item["website"] = response.urljoin(page["url"])

            if brand_info := self.brand_mapping.get(hotel.get("brand")):
                item["brand"], item["brand_wikidata"] = brand_info
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{hotel['brandName']}")
            apply_category(Categories.HOTEL, item)
            yield item
