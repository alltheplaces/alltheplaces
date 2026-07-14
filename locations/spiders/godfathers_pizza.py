import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class GodfathersPizzaSpider(Spider):
    name = "godfathers_pizza"
    item_attributes = {"brand": "Godfather's Pizza", "brand_wikidata": "Q5576353"}
    start_urls = ["https://godfathers.orderexperience.net/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        if bundle_path := response.xpath('//script[contains(@src, "/_nuxt/")]/@src').get():
            yield response.follow(bundle_path, callback=self.parse_token)

    def parse_token(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        key = re.search(r'key:"([a-f0-9]{40})"', response.text).group(1)
        yield JsonRequest(
            url=f"https://oxb.pxsweb.com/api/v1/apps/restaurants/66abfd6ce1b9d093ee0ab75d?key={key}",
            callback=self.parse_stores,
        )

    def parse_stores(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for store in response.json():
            if store.get("hide_from_picker") or not store.get("loc"):
                continue
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").removeprefix("Godfather's Pizza").strip(" -")
            item["lat"], item["lon"] = store["loc"]
            item["street_address"] = item.pop("addr_full", None)
            apply_category(Categories.RESTAURANT, item)
            yield item
