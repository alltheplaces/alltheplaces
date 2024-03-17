import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_BG, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class TechnopolisBGSpider(scrapy.Spider):
    name = "technopolis_bg"
    item_attributes = {"brand": "Technopolis", "brand_wikidata": "Q28056752", "country": "BG"}
    allowed_domains = ["www.technopolis.bg"]
    start_urls = [
        "https://api.technopolis.bg/videoluxcommercewebservices/v2/technopolis-bg/mapbox/customerpreferedstore"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # No robots.txt
        "DEFAULT_REQUEST_HEADERS": {"Accept": "application/json, text/plain, */*"},
    }

    def parse(self, response):
        for location in response.json()["storesMap"]["features"]:
            item = Feature()
            item["ref"] = location["id"]
            item["name"] = location["properties"]["name"]
            item["street_address"] = location["properties"]["contacts"]["address"]
            item["postcode"] = location["properties"]["postal"]
            item["city"] = location["properties"]["city"]
            item["lat"] = location["geometry"]["coordinates"][1]
            item["lon"] = location["geometry"]["coordinates"][0]
            item["image"] = f"https://api.technopolis.bg{location['image']}"

            item["opening_hours"] = OpeningHours()

            for worktime in (
                location["properties"]["contacts"]["worktime"]
                .replace("–", "-")
                .replace(" - ", "-")
                .replace("ч.", "")
                .replace(": ", " ")
                .replace(";", "")
                .replace(".", ":")
                .split("<br />")
            ):
                days = [sanitise_day(day, DAYS_BG) for day in worktime.split(" ")[0].split("-")]
                hours = worktime.split(" ")[1].split("-")
                if len(days) == 2:
                    item["opening_hours"].add_days_range(day_range(days[0], days[1]), hours[0], hours[1])
                else:
                    item["opening_hours"].add_range(days[0], hours[0], hours[1])
            apply_category(Categories.SHOP_ELECTRONICS, item)
            yield item
