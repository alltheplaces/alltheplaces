from json import loads
from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class LibroATSpider(AmastyStoreLocatorSpider):
    name = "libro_at"
    item_attributes = {"brand": "Libro", "brand_wikidata": "Q1823138"}
    start_urls = ["https://www.libro.at/rest/V1/mthecom/storelocator/locations"]

    def parse(self, response: Response) -> Iterable[Feature]:
        yield from self.parse_features(loads(response.xpath("/response/text()").get())["items"])

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["ref"], item["street_address"] = item.pop("name").split(": ", 1)

        yield item
