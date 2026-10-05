import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class RomanOriginalsGBSpider(Spider):
    name = "roman_originals_gb"
    item_attributes = {"brand": "Roman Originals", "brand_wikidata": "Q94579553"}
    start_urls = ["https://www.roman.co.uk/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        graph = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').get())["@graph"]
        for stores in graph:
            if stores["@type"] == "Store":
                for store in stores["department"]:
                    store.update(store.pop("location")["geo"])
                    item = DictParser.parse(store)
                    item.pop("name")
                    item["ref"] = store["areaServed"][0]["name"][0]
                    item["branch"] = item["ref"]
                    item["website"] = response.urljoin(store["url"])
                    apply_category(Categories.SHOP_CLOTHES, item)
                    yield response.follow(store["url"], self.parse_store, cb_kwargs={"item": item})

    def parse_store(self, response: Response, item: Feature) -> Any:
        # The locator's ld+json hours are the same placeholder for every store; the store page has the real ones
        hours = " ".join(response.xpath('//h2[text()="Opening times"]/following-sibling::text()').getall())
        if "Closed Until Further Notice" in hours:
            return
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours.replace(" AM", "").replace(" PM", ""))
        yield item
