from typing import Any

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class PinchAPennyUSSpider(StructuredDataSpider):
    name = "pinch_a_penny_us"
    item_attributes = {"brand": "Pinch A Penny", "brand_wikidata": "Q121436109"}
    start_urls = ["https://pinchapenny.com/api/store/search?lat=28.5&lng=-81.4"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]:
            if any(
                s in (store.get("badge") or "").lower() for s in ("coming soon", "opening soon", "temporarily closed")
            ):
                continue
            item = DictParser.parse(store)
            item["name"] = None
            item["street_address"] = merge_address_lines([item.pop("addr_full"), store["address_extended"]])
            apply_category(Categories.SHOP_SWIMMING_POOL, item)
            yield Request(store["url"], callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Any, **kwargs: Any) -> Any:
        item["opening_hours"] = OpeningHours()
        for day in response.xpath('//time[@itemprop="openingHours"]'):
            item["opening_hours"].add_ranges_from_string(" ".join(day.xpath(".//text()").getall()))
        yield item
