import json
from typing import Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class BoyersFoodMarketsUSSpider(Spider):
    name = "boyers_food_markets_us"
    item_attributes = {"brand": "Boyer's Food Markets", "brand_wikidata": "Q16985059"}
    start_urls = ["https://www.boyersfood.com/store-locator.php"]

    def parse(self, response: Response) -> Iterable[Feature]:
        script = response.xpath('//script[contains(text(), "var locations =")]/text()').get()
        coordinates = {
            location[0]: location[1:3] for location in chompjs.parse_js_object(script.split("var locations =", 1)[1])
        }

        for card in response.css("div.loc"):
            ld_data = json.loads(card.xpath('following-sibling::script[@type="application/ld+json"][1]/text()').get())
            item = LinkedDataParser.parse_ld(ld_data)

            item["branch"] = card.css("h3 a::text").get().strip()
            item.pop("name", None)
            item["website"] = response.urljoin(card.css("h3 a::attr(href)").get())
            item["ref"] = item["website"].rstrip("/").rsplit("/", 1)[-1]
            item["lat"], item["lon"] = coordinates[item["branch"]]
            item["phone"] = item["phone"].replace("FOOD (3663)", "3663")

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
