import chompjs

from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.categories import apply_yes_no, PaymentMethods
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SweetIQSpider(Spider):
    dataset_attributes = {"source": "api", "api": "sweetiq.com"}
    request_batch_size = 10

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_locations_list)

    def parse_locations_list(self, response):
        js_blob = response.xpath('//script[contains(text(), "__SLS_REDUX_STATE__")]/text()').get()
        locations_data = chompjs.parse_js_object(js_blob)
        api_url_base = locations_data["env"]["presBaseUrl"]
        api_store_locator_id = locations_data["dataSettings"]["storeLocatorId"]
        api_client_id = locations_data["dataSettings"]["clientId"]
        api_client_name = locations_data["dataSettings"]["cname"]
        location_ids = [location["properties"]["id"] for location in locations_data["dataLocations"]["collection"]["features"]]
        location_ids_batches = [location_ids[n : n + self.request_batch_size] for n in range(0, len(location_ids), self.request_batch_size)]
        for location_ids_batch in location_ids_batches:
            location_ids_batch_string = ",".join(str(location_id) for location_id in location_ids_batch)
            url = f"{api_url_base}/{api_store_locator_id}/locations-details?locale=en_US&ids={location_ids_batch_string}&clientId={api_client_id}&cname={api_client_name}"
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            if location["properties"]["isPermanentlyClosed"]:
                return
            
            item = DictParser.parse(location["properties"])
            item["ref"] = location["properties"]["branch"]
            item["lat"] = location["geometry"]["coordinates"][1]
            item["lon"] = location["geometry"]["coordinates"][0]
            item["street_address"] = ", ".join(filter(None, [location["properties"]["addressLine1"], location["properties"]["addressLine2"]]))

            item["opening_hours"] = OpeningHours()
            for day_name, time_ranges in location["properties"]["hoursOfOperation"].items():
                for time_range in time_ranges:
                    item["opening_hours"].add_range(day_name, time_range[0], time_range[1])

            payment_methods = {
                "AMEX": PaymentMethods.AMERICAN_EXPRESS,
                "American Express": PaymentMethods.AMERICAN_EXPRESS,
                "CASH ONLY": PaymentMethods.CASH,
                "CASH": PaymentMethods.CASH,
                "Cash": PaymentMethods.CASH,
                "DEBIT": PaymentMethods.DEBIT_CARDS,
                "Debit": PaymentMethods.DEBIT_CARDS,
                "DISCOVER": PaymentMethods.DISCOVER_CARD,
                "Discover": PaymentMethods.DISCOVER_CARD,
                "MASTERCARD": PaymentMethods.MASTER_CARD,
                "Mastercard": PaymentMethods.MASTER_CARD,
                "MasterCard": PaymentMethods.MASTER_CARD,
                "NFC": PaymentMethods.CONTACTLESS,
                "VISA": PaymentMethods.VISA,
                "Visa": PaymentMethods.VISA,
            }
            for payment_method in location["properties"]["paymentMethods"]:
                if payment_method in payment_methods.keys():
                    apply_yes_no(payment_methods[payment_method], item, True)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item, location, **kwargs):
        yield item
