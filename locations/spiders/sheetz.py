import scrapy

from locations.items import Feature
from locations.user_agents import BROSWER_DEFAULT


class SheetzSpider(scrapy.Spider):
    name = "sheetz"
    item_attributes = {"brand": "Sheetz", "brand_wikidata": "Q7492551"}
    allowed_domains = ["orders.sheetz.com"]
    start_urls = ["https://orders.sheetz.com/anybff/api/stores/getOperatingStates"]
    user_agent = BROSWER_DEFAULT

    def make_request(self, state, page=0):
        return scrapy.http.JsonRequest(
            f"https://orders.sheetz.com/anybff/api/stores/search?stateCode={state}&page={page}&size=15",
            data={},
            callback=self.parse_stores,
            meta={"state": state, "page": page},
        )

    def parse(self, response):
        for state in response.json()["states"].keys():
            yield self.make_request(state)

    def parse_stores(self, response):
        stores = response.json()["stores"]
        if stores == []:
            return
        for store in stores:
            features = store["features"]
            properties = {
                "ref": store["storeNumber"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "website": f'https://orders.sheetz.com/findASheetz/store/{store["storeNumber"]}',
                "street_address": store["address"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "phone": store.get("phone"),
                "opening_hours": "24/7" if features["open24x7"] else None,
                "extras": {
                    "amenity:chargingstation": features["evCharger"],
                    "amenity:fuel": True,
                    "atm": features["atm"],
                    "car_wash": features["carWash"],
                    "drive_through": store["driveThru"],
                    "fuel:diesel": features["diesel"],
                    "fuel:e0": features["e0"],
                    "fuel:e15": features["e15"],
                    "fuel:e85": features["e85"],
                    "fuel:kerosene": features["kerosene"],
                    "fuel:propane": features["propane"],
                },
            }
            yield Feature(**properties)
        yield self.make_request(response.meta["state"], 1 + response.meta["page"])
