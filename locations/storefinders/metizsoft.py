from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import FormRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

# To use, specify the Shopify URL for the brand in the format of
# {brand-name}.myshopify.com . You may then need to override the
# parse_item function to adjust extracted field values.


class MetizsoftSpider(Spider):
    """
    Metizsoft store locator app for Shopify sites, with an official website of
    https://www.metizsoft.com/product/store-locator-app

    To use this storefinder, specify the `shopify_url` attribute as observed
    on storefinder pages as having the format of "examplebrand.myshopify.com".
    You may need to override the `parse_item` function to adjust extracted
    field values.
    """

    dataset_attributes: dict = {"source": "api", "api": "storelocator.metizapps.com"}
    allowed_domains: list[str] = ["storelocator.metizapps.com"]
    shopify_url: str

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://storelocator.metizapps.com/stores/storeDataGet",
            method="POST",
            formdata={"shopData": self.shopify_url},
        )

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        if not response.json()["success"]:
            return

        for location in response.json()["data"]["result"]:
            if location["delete_status"] != "0" or location["storestatus"] != "1":
                continue
            item = DictParser.parse(location)
            item["street_address"] = ", ".join(filter(None, [location["address"], location["address2"]]))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["hour_of_operation"].replace("</br>", " "))
            yield from self.parse_item(item, location)

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        yield item
