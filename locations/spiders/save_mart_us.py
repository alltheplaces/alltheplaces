from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

BRANDS = {
    "foodmaxx.com": {"brand": "FoodMaxx", "brand_wikidata": "Q61894844"},
    "luckysupermarkets.com": {"brand": "Lucky", "brand_wikidata": "Q6698032"},
    "savemart.com": {"brand": "Save Mart", "brand_wikidata": "Q7428009"},
}


class SaveMartUSSpider(SitemapSpider):
    name = "save_mart_us"
    sitemap_urls = [
        "https://foodmaxx.com/sitemap.xml",
        "https://luckysupermarkets.com/sitemap.xml",
        "https://savemart.com/sitemap.xml",
    ]
    sitemap_rules = [(r"/stores/\d+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = chompjs.parse_js_object(
            response.xpath('//*[contains(text(),"window.__remixContext")]/text()').get()
        )["state"]["loaderData"]["routes/stores.$storeId._index"]["storeDetailsV2"]
        location.update(location.pop("location"))
        item = DictParser.parse(location)
        item.update(BRANDS[response.url.split("/")[2]])
        item["branch"] = item.pop("name")
        item["website"] = response.url
        item["phone"] = location["phoneNumbers"][0]["value"]

        item["opening_hours"] = self.parse_opening_hours(location["hours"]["weekly"])

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if rule["daily"]["type"] == "OPEN_24_HOURS":
                oh.add_range(rule["day"], "00:00", "24:00")
            else:
                oh.add_range(rule["day"], rule["daily"]["open"]["open"], rule["daily"]["open"]["close"], "%H:%M:%S")
        return oh
