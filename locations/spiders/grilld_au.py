from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GrilldAUSpider(Spider):
    name = "grilld_au"
    item_attributes = {"brand": "Grill'd", "brand_wikidata": "Q18165852"}
    allowed_domains = ["www.grilld.com.au"]
    start_urls = ["https://www.grilld.com.au/api/locations.json"]
    requires_proxy = True

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            if "TRAINING" in item["name"]:
                return
            item["street_address"] = ", ".join(
                filter(None, [location["location"]["street1"].strip(), location["location"]["street2"].strip()])
            )
            item["city"] = location["location"]["city"]
            item["state"] = location["location"]["state"]
            item["postcode"] = location["location"]["postcode"]
            apply_yes_no(Extras.DELIVERY, item, location["delivery"], False)
            item["opening_hours"] = OpeningHours()
            for day_name, day in location["hours"].items():
                if day["closed"]:
                    continue
                item["opening_hours"].add_range(day_name, day["store"]["open"], day["store"]["close"], "%I:%M %p")
            yield item
