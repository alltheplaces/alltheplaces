import json
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class RubisKESpider(JSONBlobSpider):
    name = "rubis_ke"
    item_attributes = {"brand": "Rubis", "brand_wikidata": "Q3446514"}
    start_urls = [
        "https://api.rubiskenya.com/kenolkobil/RubisMobileApiController/getStations",
    ]
    locations_key = ["respbody", "STATIONS"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        payload = {
            "respcode": 0,
            "respmsg": None,
            "techreason": None,
            "respbody": {"INSTID": "RUBISKE", "CLIENT_ID": "12345"},
        }
        for url in self.start_urls:
            yield JsonRequest(
                url,
                method="POST",
                body=json.dumps(payload),
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["STATION_ID"]

        if feature["STSN_COORDINATES"]:
            item["lat"] = feature["STSN_COORDINATES"][0]["LATI"]
            item["lon"] = feature["STSN_COORDINATES"][0]["LONG"]

        item["branch"] = feature["STATION_NAME"].removeprefix("Rubis ")

        try:
            item["phone"] = feature["STATION_PHONEs"][0]["NUMBER_1"]
        except (KeyError, IndexError, TypeError):
            pass

        if feature["STATION_TYPE"] == "STATION":
            apply_category(Categories.FUEL_STATION, item)
        elif feature["STATION_TYPE"] == "SHOP":
            apply_category(Categories.SHOP_CONVENIENCE, item)
            item["name"] = "Rubis Enjoy"
        else:
            return

        self.crawler.stats.inc_value(f"atp/{self.name}/station_type/{feature['STATION_TYPE']}")

        if feature["STSN_AMENITIES"]:
            amenities = [amenity["AMENI_NAME"] for amenity in feature["STSN_AMENITIES"]]

            apply_yes_no(Fuel.DIESEL, item, "Diesel" in amenities)
            apply_yes_no("fuel:petrol", item, "Petrol" in amenities)
            apply_yes_no(Extras.CAR_WASH, item, "CAR WASH" in amenities)
            apply_yes_no(PaymentMethods.MPESA, item, "We Accept M-Pesa" in amenities)

            for amenity in amenities:
                self.crawler.stats.inc_value(f"atp/{self.name}/amenities/{amenity}")

        yield item
