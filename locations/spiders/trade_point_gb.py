from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class TradePointGBSpider(Spider):
    name = "trade_point_gb"
    item_attributes = {"brand": "TradePoint", "brand_wikidata": "Q115211017"}
    start_urls = ["https://api.kingfisher.com/v1/mobile/stores/TPUK?nearLatLong=0,0&page[size]=1000"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Authorization": "Atmosphere atmosphere_app_id=kingfisher-LTbGHXKinHaJSV86nEjf0KnO70UOVE6UcYAswLuC"
        }
    }

    def parse(self, response, **kwargs):
        for store in response.json()["data"]:
            if store["type"] != "store":
                continue

            item = Feature()

            item["ref"] = store["id"]
            item["website"] = "https://www.trade-point.co.uk/store/" + store["id"]
            item["name"] = store["attributes"]["store"]["name"]

            item["lat"] = store["attributes"]["store"]["geoCoordinates"]["coordinates"]["latitude"]
            item["lon"] = store["attributes"]["store"]["geoCoordinates"]["coordinates"]["longitude"]

            item["phone"] = store["attributes"]["store"]["contactPoint"]["telephone"]
            item["extras"] = {
                "email": store["attributes"]["store"]["contactPoint"]["email"],
                "fax": store["attributes"]["store"]["contactPoint"]["faxNumber"],
                "storeType": store["attributes"]["store"]["storeType"],
            }

            item["addr_full"] = ", ".join(
                filter(
                    None,
                    store["attributes"]["store"]["geoCoordinates"]["address"]["lines"],
                )
            )
            item["postcode"] = store["attributes"]["store"]["geoCoordinates"]["postalCode"]
            item["country"] = store["attributes"]["store"]["geoCoordinates"]["countryCode"]

            item["opening_hours"] = OpeningHours()
            for rule in store["attributes"]["store"]["openingHoursSpecifications"]:
                if rule.get("opens") and rule.get("closes"):
                    item["opening_hours"].add_range(rule["dayOfWeek"], rule["opens"][:5], rule["closes"][:5])

            yield item
