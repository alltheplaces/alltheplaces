import json
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CakeBoxGBSpider(SitemapSpider):
    name = "cake_box_gb"
    item_attributes = {"brand": "Cake Box", "brand_wikidata": "Q110057905"}
    sitemap_urls = ["https://www.cakebox.com/sitemap-stores.xml"]
    sitemap_rules = [(r"/storelocator/[^/]+\.data$", "parse")]

    def sitemap_filter(self, entries: Iterable[dict]) -> Iterable[dict]:
        for entry in entries:
            # The React Router route data holds every field the rendered page omits.
            entry["loc"] = entry["loc"] + ".data"
            yield entry

    def parse(self, response: Response, **kwargs: Any) -> Any:
        payload = json.loads(response.text.split("\n", 1)[0])

        def resolve(reference: int) -> Any:
            if reference < 0:
                return None
            value = payload[reference]
            if isinstance(value, dict):
                return {payload[int(key.removeprefix("_"))]: resolve(child) for key, child in value.items()}
            if isinstance(value, list):
                return [resolve(child) for child in value]
            return value

        def descend(reference: int, name: str) -> int:
            return next(
                child for key, child in payload[reference].items() if payload[int(key.removeprefix("_"))] == name
            )

        reference = 0
        for name in ("routes/storelocator.$handle", "data", "store"):
            reference = descend(reference, name)
        location = resolve(reference)

        location.pop("id")  # A Shopify GID, which would win over storeId as the ref.
        location.pop("region")  # A marketing region ("Midlands", "South"), not an administrative one.

        item = DictParser.parse(location)
        item["branch"] = item.pop("name").removeprefix("Cake Box ")
        item["website"] = response.url.removesuffix(".data")
        item["image"] = (location["image"] or {}).get("url")

        item["opening_hours"] = OpeningHours()
        for day, rule in location["openingHours"].items():
            if rule["isClosed"]:
                item["opening_hours"].set_closed(day)
                continue
            for interval in rule["intervals"]:
                if interval["open"] < interval["close"]:
                    item["opening_hours"].add_range(day, interval["open"], interval["close"])

        apply_yes_no(Extras.DELIVERY, item, "delivery" in location["services"])
        apply_category(Categories.SHOP_PASTRY, item)

        yield item
