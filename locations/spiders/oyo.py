from typing import Any, AsyncIterator, Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class OyoSpider(StructuredDataSpider):
    name = "oyo"
    item_attributes = {"brand": "OYO", "brand_wikidata": "Q24906315"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Any]:
        for country in ["ae", "br", "ca", "gb", "id", "in", "mx", "my", "np", "sa", "th", "us", "vn"]:
            yield scrapy.Request("https://www.oyorooms.com/{}/allcities/".format(country), self.parse_all_cities)

    def parse_all_cities(self, response: Response, **kwargs: Any) -> Any:
        for link in response.xpath("//a/@href").extract():
            if "/hotels-in-" in link:
                yield scrapy.Request(response.urljoin(link), self.parse_hotels_in_first_page)

    def parse_hotels_in_first_page(self, response: Response, **kwargs: Any) -> Any:
        for link in response.xpath("//a/@href").extract():
            if "?page=" in link:
                yield scrapy.Request(response.urljoin(link), self.parse_hotel_cards)
        yield from self.parse_hotel_cards(response)

    def parse_hotel_cards(self, response: Response, **kwargs: Any) -> Any:
        for link in response.xpath('//meta[@itemprop="url"]/@content').getall():
            yield scrapy.Request(link)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["phone"] = None
        apply_category(Categories.HOTEL, item)
        yield item
