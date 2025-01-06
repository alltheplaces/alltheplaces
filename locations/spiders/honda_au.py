from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class HondaAUSpider(Spider):
    name = "honda_au"
    item_attributes = {"brand": "Honda", "brand_wikidata": "Q9584"}
    allowed_domains = ["www.honda.com.au"]
    start_urls = ["https://www.honda.com.au/api/locateDealer/Dealerships/get"]
    require_proxy = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response) -> Iterable[Feature]:
        for dealership in response.json():
            for feature in dealership["Locations"]:
                if feature["Type"] == "Trade Parts":
                    # Ignore as already covered by "Parts".
                    continue

                item = DictParser.parse(feature)
                item["ref"] = dealership["DealerNo"] + "_" + feature["Type"]
                item.pop("name", None)
                item["branch"] = dealership["Name"]

                if feature["Type"] == "Sales":
                    apply_category(Categories.SHOP_CAR, item)
                elif feature["Type"] == "Service":
                    apply_category(Categories.SHOP_CAR_REPAIR, item)
                elif feature["Type"] == "Parts":
                    apply_category(Categories.SHOP_CAR_PARTS, item)

                item["street_address"] = clean_address([feature.get("AddressLine1"), feature.get("AddressLine2")])
                item["city"] = feature.get("AddressSuburb")
                item["state"] = feature.get("AddressState")
                item["postcode"] = feature.get("AddressPostcode")
                if dealership.get("Website"):
                    item["website"] = "https://www.honda.com.au" + dealership["Website"]

                item["opening_hours"] = OpeningHours()
                hours_string = ""
                for day_hours in feature["WorkingHoursArray"]:
                    day_name = day_hours["day"]
                    time_ranges = ", ".join(day_hours["time"])
                    hours_string = f"{hours_string} {day_name}: {time_ranges}"
                item["opening_hours"].add_ranges_from_string(hours_string)

                yield item
