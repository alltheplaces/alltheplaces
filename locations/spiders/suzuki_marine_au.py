from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SuzukiMarineAUSpider(Spider):
    name = "suzuki_marine_au"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}

    def start_requests(self):
        yield JsonRequest(url="https://www.suzukimarine.com.au/find-dealers/dealersByState?state=all")

    def parse(self, response, **kwargs):
        for feature in response.json():
            item = DictParser.parse(feature)
            if "Link" in feature:
                item["website"] = "https://www.suzukimarine.com.au" + feature["Link"]

            if "Services" in feature:
                if "0" in feature["Services"]:
                    apply_category(Categories.SHOP_BOAT, item)
                if "1" in feature["Services"]:
                    apply_category({"boat:repair": "yes"}, item)
                if "2" in feature["Services"]:
                    apply_category({"boat:parts": "yes"}, item)

            if "ServiceHours" in feature and feature["ServiceHours"] is not None:
                item["opening_hours"] = OpeningHours()

                # "ServiceHours": "<p>Mon - Fri: 8:00am - 5:00pm<br>Sat: 8:00am - 12:00pm<br>Sun: Closed</p>",
                item["opening_hours"].add_ranges_from_string(
                    feature["ServiceHours"].replace("<br>", ", ").replace("<p>", "").replace("</p>", "")
                )

            if "LatLong" in feature:
                item["lat"], item["lon"] = feature["LatLong"].split(",")

            yield item
