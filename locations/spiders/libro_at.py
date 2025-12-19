from json import loads
from typing import AsyncIterator, Iterable

from scrapy import Selector
from scrapy.http import Request, Response

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class LibroATSpider(AmastyStoreLocatorSpider):
    name = "libro_at"
    item_attributes = {"brand": "Libro", "brand_wikidata": "Q1823138"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url="https://www.libro.at/rest/V1/mthecom/storelocator/locations")

    def parse(self, response: Response) -> Iterable[Feature]:
        yield from self.parse_features(loads(response.xpath("/response/text()").get())["items"])

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["ref"], item["street_address"] = item.pop("name").split(": ", 1)
        item["addr_full"] = clean_address(popup_html.xpath("//span/text()").getall()).removesuffix(", Filiale wählen")
        item["website"] = f'https://www.libro.at/filialfinder/{item["ref"]}/'
        yield item
