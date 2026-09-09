from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class BankomatSESpider(Spider):
    name = "bankomat_se"
    item_attributes = {"brand": "Bankomat", "brand_wikidata": "Q10426078"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url="https://www.bankomat.se/proxy.php?service=places")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)  # maps identifier->ref, city, zipcode->postcode, address1->street_address
            item["geometry"] = location["point"]

            # When address2 is present, address1 is the host venue (e.g. "Avesta galleria") and address2 the street.
            if location.get("address2"):
                item["located_in"] = location["address1"]
                item["street_address"] = location["address2"]

            services = {service["identifier"] for service in location.get("services", []) if service.get("available")}
            apply_yes_no(Extras.CASH_IN, item, "deposit" in services)
            apply_yes_no(PaymentMethods.CONTACTLESS, item, "NFC" in services)
            if {machine.get("opening_hours") for machine in location.get("machines", [])} == {"Dygnet runt"}:
                item["opening_hours"] = "24/7"  # "Dygnet runt" = around the clock; other freeform hours are skipped

            apply_category(Categories.ATM, item)
            yield item
