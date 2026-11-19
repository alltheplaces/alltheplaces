from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.google_url import extract_google_position
from locations.linked_data_parser import LinkedDataParser


class JerseyMikesCASpider(Spider):
    name = "jersey_mikes_ca"
    item_attributes = {"brand": "Jersey Mike's Subs", "brand_wikidata": "Q6184897"}
    start_urls = ["https://www.jerseymikes.ca/locations"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for ld in LinkedDataParser.iter_linked_data(response):
            if ld.get("@type") != "ItemList":
                continue

            # JSON-LD and the cards list the stores in the same order
            for element, card in zip(ld.get("itemListElement", []), response.xpath('//li[@class="location-card"]')):
                item = DictParser.parse(element["item"])
                item["website"] = None
                item["branch"] = item.pop("name").removeprefix("Jersey Mike's Subs - ")
                # Only take the card's data if its city matches the JSON-LD city
                if card.xpath(".//h3/text()").get("").strip() == item["city"]:
                    item["phone"] = card.xpath('.//p[@class="location-phone"]/a/text()').get()
                    extract_google_position(item, Selector(text=card.get()))
                apply_category(Categories.FAST_FOOD, item)

                yield item
