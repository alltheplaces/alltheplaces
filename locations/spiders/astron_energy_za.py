from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider

ASTRON_PROPERTIES = {
    "atm": Extras.ATM,
    "toilets": Extras.TOILETS,
    # "freshStop":
    # "truckSize":
    # "status": # appears to always be astron-station
    # "truckStop":
    # "ucount": false,
    # "aramex": false,
    "carwash": Extras.CAR_WASH,
    # "House Of Coffees":
    # "lavazza":
    # "pargo":
    # "rewards":
    # "seattle":
    # "starcard":
    # "astron Energy Rewards":
    # "uCount Rewards":
    # "coffee":
    # "courier Services":
    # "convenience Partner":
    # "crispy Chicken":
    # "fast Food":
    # "grill 2 Go":
    # "manhattan":
    # "halaal":
    # "restaurant":
    # "the Courier Guy":
    "wiFi": Extras.WIFI,
    # "vehicle Service Repair Workshop":
    # "petrol":
}


class AstronEnergyZASpider(JSONBlobSpider):
    name = "astron_energy_za"
    item_attributes = {
        "brand": "Astron Energy",
        "brand_wikidata": "Q120752181",
        "extras": Categories.FUEL_STATION.value,
    }
    start_urls = ["https://www.astronenergy.co.za/umbraco/api/station/Stations"]
    locations_key = "stations"

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse)

    def pre_process_data(self, location):
        for key in ["name", "town", "suburb", "region", "physicalAddress"]:
            location["properties"]["station"][key] = location["properties"]["station"][key].title()
        for tag, value in location["properties"]["station"].items():
            if tag not in location:
                location[tag] = value
        location["street_address"] = location.pop("physicalAddress")

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        if len(location["images"]) > 0:
            item["image"] = "https://www.astronenergy.co.za" + location["images"][0]
        for tag, service in ASTRON_PROPERTIES.items():
            apply_yes_no(service, item, location["properties"].get(tag), False)
        item["opening_hours"] = OpeningHours()
        if location["workingHours"] == "24hrs":
            item["opening_hours"].add_days_range(DAYS, "00:00", "24:00")
        else:
            item["opening_hours"].add_ranges_from_string("Mo-Su " + location["workingHours"])
        yield item
