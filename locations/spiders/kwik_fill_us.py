from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class KwikFillUSSpider(Spider):
    name = "kwik_fill_us"
    item_attributes = {"brand": "Kwik Fill", "brand_wikidata": "Q108477252"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.kwikfill.com/api/v1/store?page={}&size=100".format(page),
            headers={"x-api-key": "WjSyKCnwXxHx"},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]["items"]:
            item = Feature()
            item["ref"] = location["identifier"]
            item["lat"] = location["data"]["sLat"]
            item["lon"] = location["data"]["sLon"]
            item["street_address"] = merge_address_lines([location["data"]["sAddr1"], location["data"]["sAddr2"]])
            item["city"] = location["data"]["sCity"]
            item["postcode"] = location["data"]["sZip"]
            item["state"] = location["data"]["sState"]
            item["phone"] = location["data"]["sPhone"]
            item["extras"]["fax"] = location["data"]["sFax"]

            if location["data"]["sDieselPrice"]:
                item["extras"]["charge:diesel"] = "{} USD/1 gallon".format(location["data"]["sDieselPrice"])

            # TODO:item["extras"]["charge:"] = "{} USD/1 gallon".format(location["data"]["sGasPrice"])

            features = location.get("features") or []

            if "24 Hours" in features:
                item["opening_hours"] = "24/7"

            apply_yes_no(Extras.ATM, item, "ATM" in features)
            apply_yes_no(Fuel.DIESEL, item, "Diesel" in features)
            apply_yes_no(Fuel.ETHANOL_FREE, item, "Ethanol Free" in features)
            apply_yes_no(Fuel.KEROSENE, item, "Kerosene" in features)
            apply_yes_no("sells:lottery", item, "Lottery" in features)
            apply_yes_no(Fuel.PROPANE, item, "Propane" in features)

            apply_category(Categories.FUEL_STATION, item)

            yield item

        pagination = response.json()["response"]["pagination"]
        if pagination["page"] < pagination["total"]:
            yield self.make_request(pagination["page"] + 1)
