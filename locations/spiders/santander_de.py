from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature


class SantanderDESpider(Spider):
    name = "santander_de"
    item_attributes = {"brand": "Santander", "brand_wikidata": "Q875292"}
    start_urls = ["https://service.santander.de/webapps/apps/filialen/getAllMarkers"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json()["branches"]:
            if location["is_permanently_closed"]:
                continue

            item = Feature()
            item["ref"] = location["centercode"]
            item["lat"] = location["geoloc_lat"]
            item["lon"] = location["geoloc_lon"]
            item["branch"] = location["name"]
            item["street_address"] = location["street"]
            item["postcode"] = location["postcode"]
            item["city"] = location["city"]
            item["state"] = location["state"]
            item["email"] = location["email"]
            item["phone"] = location["phone"]
            item["extras"]["fax"] = location["fax"]

            item["extras"]["check_date"] = location["lastmodified"]["date"]

            item["opening_hours"] = OpeningHours()
            for day in map(str.lower, DAYS_3_LETTERS):
                for zone in ["1", "2"]:
                    item["opening_hours"].add_range(
                        day, location[f"open_{day}{zone}_start"], location[f"open_{day}{zone}_end"]
                    )

            apply_category(Categories.BANK, item)

            yield item

        for location in response.json()["atms"]:
            if location["bank"] != "Santander":
                continue

            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["geoloc_lat"]
            item["lon"] = location["geoloc_lon"]
            item["street_address"] = location["street"]
            item["postcode"] = location["postcode"]
            item["city"] = location["city"]

            apply_category(Categories.ATM, item)

            yield item
