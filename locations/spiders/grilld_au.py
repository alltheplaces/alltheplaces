from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GrilldAUSpider(Spider):
    name = "grilld_au"
    item_attributes = {"brand": "Grill'd", "brand_wikidata": "Q18165852", "extras": Categories.FAST_FOOD.value}
    allowed_domains = ["www.grilld.com.au"]
    start_urls = ["https://api.digital.grilld.com.au/v1/Restaurants/nearby?lat=-23.12&lng=132.13&limit=10000"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            if location.get("slug"):
                item["website"] = "https://grilld.com.au/restaurants/" + location["slug"]

            hours_string = ""
            for day_hours in location.get("hours", []):
                if day_hours.get("isClosed"):
                    continue
                hours_string = "{} {}: {}".format(hours_string, day_hours["name"], day_hours["description"])
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
