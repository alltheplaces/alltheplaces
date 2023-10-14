from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


# Similar to KfcAmrestSpider
class PizzaHutAmrestSpider(Spider):
    name = "pizza_hut_amrest"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = [
        "https://api.amrest.eu/amdv/ordering-api/PH_PL",
        "https://api.amrest.eu/amdv/ordering-api/PH_HU",
        "https://api.amrest.eu/amdv/ordering-api/PH_CZ",
    ]

    def start_requests(self):
        for root_url in self.start_urls:
            country = root_url.split("/")[-1].split("_")[-1].lower()
            yield JsonRequest(
                url=f"https://api.amrest.eu/amdv/ordering-api/PH_{country.upper()}/rest/v1/auth/get-token",
                data={
                    "deviceUuid": "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF",
                    "deviceUuidSource": "FINGERPRINT",
                    "source": "WEB_PH",
                },
                headers={
                    "User-Agent": BROWSER_DEFAULT,
                    "Brand": "PH",
                },
                callback=self.parse_token,
                meta=dict(country=country),
            )

    def parse_token(self, response, **kwargs):
        yield Request(
            url=f"https://api.amrest.eu/amdv/ordering-api/PH_{response.meta['country'].upper()}/rest/v2/restaurants/",
            headers={
                "Referer": "https://pizzahut.pl/",
                "Brand": "PH",
                "Authorization": f"Bearer {response.json()['token']}",
            },
            callback=self.parse_api,
            meta=response.meta,
        )

    def parse_api(self, response, **kwargs):
        for location in response.json()["restaurants"]:
            item = DictParser.parse(location)
            item["country"] = response.meta["country"]
            item["street"] = location["addressStreet"]
            yesNoAttributes = {
                "driveThru": Extras.DRIVE_THROUGH,
                "garden": Extras.OUTDOOR_SEATING,
                "delivery": Extras.DELIVERY,
                "wifi": Extras.WIFI,
                "takeaway": Extras.TAKEAWAY,
            }
            for key, extra in yesNoAttributes.items():
                apply_yes_no(attribute=extra, item=item, state=location[key], apply_positive_only=False)
            openHours = location["openHours"][0]  # always one item
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(
                days=DAYS, open_time=openHours["openFrom"], close_time=openHours["openTo"]
            )
            for f in location["filters"]:
                if f["key"] == "waiter_service":
                    apply_category(Categories.RESTAURANT if f["available"] else Categories.FAST_FOOD, item)
            yield item
