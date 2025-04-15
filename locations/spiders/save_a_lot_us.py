from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours


class SaveALotUSSpider(Spider):
    name = "save_a_lot_us"
    item_attributes = {"brand": "Save-A-Lot", "brand_wikidata": "Q7427972", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["savealot.com"]
    download_delay = 0.2

    def start_requests(self):
        # API returns stores within 25 miles of a provided WGS84 coordinate.
        for lat, lon in country_iseadgg_centroids(["US"], 24):
            yield JsonRequest(url=f"https://savealot.com/?lat={lat}&lng={lon}&_data=root")

    def parse(self, response):
        if stores := response.json()["storeList"]:
            if locations := stores.get("stores"):
                for location in locations:
                    location.update(location.pop("location"))
                    item = DictParser.parse(location)
                    item["branch"] = item.pop("name", None)
                    item["website"] = "https://savealot.com/stores/" + location["storeId"]

                    for phone_number in location["phoneNumbers"]:
                        if phone_number["description"] == "Main":
                            item["phone"] = phone_number["value"]
                            break

                    item["opening_hours"] = OpeningHours()
                    for day_hours in location["hours"]["weekly"]:
                        hours = day_hours["daily"]
                        if "24_HOURS" in hours["type"]:
                            item["opening_hours"].add_range(day_hours["day"], "00:00", "24:00", "%H:%M")
                        else:
                            item["opening_hours"].add_range(
                                day_hours["day"], hours["open"]["open"], hours["open"]["close"], "%H:%M:%S"
                            )

                    yield item
