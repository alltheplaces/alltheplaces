from typing import Any
from urllib.parse import urljoin, urlparse

from scrapy.http import JsonRequest, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


# Bridgestone Retail Operations(BSRO): https://www.bsro.com/
# Part of Bridgestone Americas: https://www.bridgestoneamericas.com/en/company/businesses/services
class BsroSpider(CrawlSpider):
    name = "bsro"
    BRANDS = {
        "FCAC": {"brand": "Firestone", "brand_wikidata": "Q420837"},
        "TP": {"brand": "Tires Plus", "brand_wikidata": "Q64015091"},
        "WW": {"brand": "Wheel Works", "brand_wikidata": "Q121088283"},
        "HTP": {"brand": "Hibdon Tires Plus"},
    }
    start_urls = [
        "https://www.firestonecompleteautocare.com/local/",
        "https://www.tiresplus.com/local/",
    ]
    rules = [
        Rule(
            LinkExtractor(restrict_xpaths='//*[contains(text(),"State")]/following-sibling::div[1]'),
        ),
        Rule(
            LinkExtractor(restrict_xpaths='//*[contains(text(),"Cities")]/following-sibling::div[1]'), callback="parse"
        ),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Retrieve store IDs from city page and then make store-wise API call to fetch store details
        for store_id in response.xpath("//@data-store").getall():
            yield JsonRequest(
                url=f"https://{urlparse(response.url).hostname}/bsro/services/store/details/{store_id}",
                callback=self.parse_store,
            )

    def parse_store(self, response: Response) -> Any:
        if store := response.json().get("data"):
            if store["temporarilyClosed"] == "Y":
                return
            store["street-address"] = store.pop("address", "")
            item = DictParser.parse(store)
            item["website"] = urljoin(f"https://{urlparse(response.url).hostname}", store.get("localPageURL", ""))
            item["extras"]["fax"] = store.get("fax")
            item["opening_hours"] = OpeningHours()
            for rule in store.get("hours", []):
                if day := sanitise_day(rule.get("weekDay")):
                    item["opening_hours"].add_range(day, rule.get("openTime"), rule.get("closeTime"))
            if store_type := store.get("storeType"):
                if brand_info := self.BRANDS.get(store_type.replace("TPL", "TP")):  # TPL: Tires Plus Licensee
                    item.update(brand_info)
                if store_type == "HTP":
                    apply_category(Categories.SHOP_TYRES, item)
            yield item
