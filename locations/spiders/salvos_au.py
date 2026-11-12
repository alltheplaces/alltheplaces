from typing import Iterable

from chompjs import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class SalvosAUSpider(JSONBlobSpider, PlaywrightSpider):
    name = "salvos_au"
    item_attributes = {"brand": "Salvos", "brand_wikidata": "Q120646407"}
    start_urls = ["https://www.salvosstores.com.au/stores"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS  # Playwright helps to avoid http 429

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        return DictParser.get_nested_key(
            chompjs.parse_js_object(
                response.xpath('//script[contains(text(), "_geoloc")]/text()').get("").split("=", 1)[-1]
            ),
            "hits",
        )

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("_geoloc", {}))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if "ONLINE STORE ONLY" in feature["address"].upper():
            return
        item["branch"] = item.pop("name", None)
        item["state"] = feature.get("address_state")
        if slug := feature.get("url_key"):
            item["website"] = f'https://www.salvosstores.com.au/stores/{slug.strip("/")}'

        trading_hours = feature.get("trading_hours") or []
        try:
            item["opening_hours"] = self.parse_opening_hours(trading_hours)
        except Exception as e:
            self.logger.warning(f"Failed to parse hours: {trading_hours}, {e}")

        apply_category(Categories.SHOP_CHARITY, item)
        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            for day, hours in rule.items():
                if hours.get("isOpen") is False:
                    opening_hours.set_closed(day)
                    continue
                opening_hours.add_range(day, hours["openingTime"], hours["closingTime"], "%H:%M:%S")
        return opening_hours
