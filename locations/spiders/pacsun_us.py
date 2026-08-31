import json
from typing import Any, Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PacsunUSSpider(Spider):
    name = "pacsun_us"
    item_attributes = {"brand": "PacSun", "brand_wikidata": "Q7121857"}
    custom_settings = {"USER_AGENT": "Mozilla/5.0"}
    start_urls = ["https://www.pacsun.com/on/demandware.store/Sites-pacsun-Site/default/Stores-FindStores?radius=30000"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        data = response.json()
        cards = {
            card.xpath("./@id").get(): card
            for card in Selector(text=data["storesResultsHtml"]).xpath('//div[contains(@class, "store-result")]')
        }
        for location in json.loads(data["locations"]):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")

            if card := cards.get(location["storeID"]):
                item["street_address"] = merge_address_lines(
                    card.xpath('.//span[contains(@class, "store-locator-address")]/text()').getall()
                )
                city, state, postcode = (
                    card.xpath('.//address/a/div/span[@class="store-locator-details"]/text()').getall() + [None] * 3
                )[:3]
                item["city"] = city.strip().rstrip(",") if city else None
                item["state"] = state.strip() if state else None
                item["postcode"] = postcode.strip() if postcode else None
                item["phone"] = card.xpath('.//a[contains(@class, "storelocator-phone")]/text()').get("").strip()
                item["website"] = card.xpath('.//a[contains(@class, "store-map")]/@href').get()

                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(
                    "; ".join(card.xpath('.//div[@class="hours"]/text()').getall())
                )

            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
