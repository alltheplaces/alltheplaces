import scrapy

from locations.hours import DAYS_BG, OpeningHours
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
                .replace("ч.", "")
                .replace(".", ":")
                .split("<br />")
            ):
                item["opening_hours"].add_ranges_from_string(worktime, days=DAYS_BG)
            yield item
