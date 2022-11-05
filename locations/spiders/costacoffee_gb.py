import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


def yes_or_no(condition):
    return "yes" if condition else "no"


class CostaCoffeeGBSpider(scrapy.Spider):
    name = "costacoffee_gb"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["www.costa.co.uk"]
    start_urls = ["https://www.costa.co.uk/api/locations/stores"]

    def parse(self, response):
        for store_data in response.json()["stores"]:
            if store_data.get("storeStatus") != "TRADING":
                continue

            store_data["address"] = store_data["storeAddress"]

            item = DictParser.parse(store_data)

            item["ref"] = store_data["storeNo8Digit"]
            item["name"] = store_data["storeNameExternal"]
            item["street_address"] = ", ".join(
                filter(
                    None,
                    [
                        store_data["storeAddress"]["addressLine1"],
                        store_data["storeAddress"]["addressLine2"],
                        store_data["storeAddress"]["addressLine3"],
                    ],
                ),
            )

            opening_hours = OpeningHours()
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                if (
                    store_data["storeOperatingHours"]["open" + day] != ""
                    and store_data["storeOperatingHours"]["close" + day] != ""
                ):
                    try:
                        opening_hours.add_range(
                            day[0:2],
                            store_data["storeOperatingHours"]["open" + day],
                            store_data["storeOperatingHours"]["close" + day],
                        )
                    except:
                        pass

            item["opening_hours"] = opening_hours.as_opening_hours()
            item["extras"] = {"email": store_data["email"]}

            for storeFacility in store_data["storeFacilities"]:
                if storeFacility["name"] == "Wifi":
                    if storeFacility["active"]:
                        item["extras"]["internet_access"] = "wlan"
                    else:
                        item["extras"]["internet_access"] = "no"
                elif storeFacility["name"] == "Disabled WC":
                    if storeFacility["active"]:
                        item["extras"]["toilets"] = "yes"
                        item["extras"]["toilets:wheelchair"] = "yes"
                    else:
                        item["extras"]["toilets:wheelchair"] = "no"
                elif storeFacility["name"] == "Baby Changing":
                    item["extras"]["changing_table"] = yes_or_no(
                        storeFacility["active"]
                    )
                elif storeFacility["name"] == "Disabled Access":
                    item["extras"]["wheelchair"] = yes_or_no(storeFacility["active"])
                elif storeFacility["name"] == "Drive Thru":
                    item["extras"]["drive_through"] = yes_or_no(storeFacility["active"])
                elif storeFacility["name"] == "Delivery":
                    item["extras"]["delivery"] = yes_or_no(storeFacility["active"])

            if store_data["storeType"] == "COSTA EXPRESS":
                item["brand"] = "Costa Express"
                item["extras"]["amenity"] = "vending_machine"
                item["extras"]["vending"] = "coffee"
            else:
                item["extras"]["amenity"] = "cafe"
                item["extras"]["cuisine"] = "coffee_shop"

            yield item
