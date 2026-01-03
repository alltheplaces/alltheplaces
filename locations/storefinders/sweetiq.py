from typing import AsyncIterator, Iterable

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import JsonRequest, Request, TextResponse

from locations.categories import PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class SweetIQSpider(Spider):
    """
    SweetIQ (now owned by uberall) provides a store locator
    https://sweetiq.com/our-products/store-locator-microsites/

    Provide `start_urls`, which will then automatically extract API keys and other data.
    """

    start_urls: list[str] = []
    dataset_attributes: dict = {"source": "api", "api": "sweetiq.com"}
    request_batch_size: int = 10

    async def start(self) -> AsyncIterator[Request]:
        if len(self.start_urls) != 1:
            raise ValueError("Specify one URL in the start_urls list attribute.")
            return
        yield Request(url=self.start_urls[0], callback=self.parse_locations_list)

    def parse_locations_list(self, response: TextResponse) -> Iterable[JsonRequest]:
        js_blob = response.xpath('//script[contains(text(), "__SLS_REDUX_STATE__")]/text()').get()
        locations_data = parse_js_object(js_blob)
        api_url_base = locations_data["env"]["presBaseUrl"]
        api_store_locator_id = locations_data["dataSettings"]["storeLocatorId"]
        api_client_id = locations_data["dataSettings"]["clientId"]
        api_client_name = locations_data["dataSettings"]["cname"]
        location_ids = [
            location["properties"]["id"] for location in locations_data["dataLocations"]["collection"]["features"]
        ]
        location_ids_batches = [
            location_ids[n : n + self.request_batch_size] for n in range(0, len(location_ids), self.request_batch_size)
        ]
        for location_ids_batch in location_ids_batches:
            location_ids_batch_string = ",".join(str(location_id) for location_id in location_ids_batch)
            url = f"{api_url_base}/{api_store_locator_id}/locations-details?locale=en_US&ids={location_ids_batch_string}&clientId={api_client_id}&cname={api_client_name}"
            yield JsonRequest(url=url)

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json()["features"]:
            self.pre_process_data(location)

            if location["properties"]["isPermanentlyClosed"]:
                return

            item = DictParser.parse(location["properties"])
            item["ref"] = location["properties"]["branch"]
            item["geometry"] = location["geometry"]
            item["street_address"] = ", ".join(
                filter(None, [location["properties"]["addressLine1"], location["properties"]["addressLine2"]])
            )

            item["opening_hours"] = OpeningHours()
            for day_name, time_ranges in location["properties"]["hoursOfOperation"].items():
                for time_range in time_ranges:
                    item["opening_hours"].add_range(day_name, time_range[0], time_range[1])

            item["extras"] = {}
            if future_opening_date := location["properties"]["futureOpeningDate"]:
                item["extras"]["start_date"] = future_opening_date

            payment_methods = {
                "AMEX": PaymentMethods.AMERICAN_EXPRESS,
                "AMERICAN EXPRESS": PaymentMethods.AMERICAN_EXPRESS,
                "CASH ONLY": PaymentMethods.CASH,
                "CASH": PaymentMethods.CASH,
                "DEBIT": PaymentMethods.DEBIT_CARDS,
                "DISCOVER": PaymentMethods.DISCOVER_CARD,
                "MASTERCARD": PaymentMethods.MASTER_CARD,
                "NFC": PaymentMethods.CONTACTLESS,
                "VISA": PaymentMethods.VISA,
            }
            for payment_method in location["properties"]["paymentMethods"]:
                if payment_method.upper() in payment_methods.keys():
                    apply_yes_no(payment_methods[payment_method.upper()], item, True)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        yield item

    def pre_process_data(self, location: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""
