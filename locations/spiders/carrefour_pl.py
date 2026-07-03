import json
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.carrefour_fr import CARREFOUR_EXPRESS, CARREFOUR_MARKET, CARREFOUR_SUPERMARKET
from locations.user_agents import BROWSER_DEFAULT


class CarrefourPLSpider(JSONBlobSpider, PlaywrightSpider):
    name = "carrefour_pl"
    start_urls = ["https://www.carrefour.pl/sklepy"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False} | DEFAULT_PLAYWRIGHT_SETTINGS
    requires_proxy = True

    brands = {
        "Carrefour Express Zielony ": CARREFOUR_EXPRESS,
        "Carrefour Express": CARREFOUR_EXPRESS,
        "Hipermarket": CARREFOUR_SUPERMARKET,
        "Carrefour Market": CARREFOUR_MARKET,
        "Supermarket Franczyzowy": CARREFOUR_MARKET,
        "Globi": {"brand": "Globi", "brand_wikidata": "Q11751761", "category": Categories.SHOP_CONVENIENCE},
        "Carrefour": CARREFOUR_SUPERMARKET,
    }

    def extract_json(self, response: TextResponse) -> list[dict]:
        return DictParser.get_nested_key(
            json.loads(response.xpath('//script[@id="__NEXT_DATA__"]//text()').get()), "shops"
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["uuid"]
        item.pop("name", None)
        for brand_key in self.brands:
            if feature["displayName"].startswith(brand_key):
                brand_info = self.brands[brand_key]
                item["brand"] = brand_info["brand"]
                item["brand_wikidata"] = brand_info["brand_wikidata"]
                apply_category(brand_info["category"], item)
                break
        item["website"] = f'https://www.carrefour.pl/sklep/{feature["slug"].strip("/")}'
        yield item
