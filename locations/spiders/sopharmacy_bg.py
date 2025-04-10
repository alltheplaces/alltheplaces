import scrapy

from locations.hours import DAYS_BG, OpeningHours
from locations.items import Feature


class SopharmacyBGSpider(scrapy.Spider):
    name = "sopharmacy_bg"
    item_attributes = {"brand": "SOpharmacy", "brand_wikidata": "Q108852081"}
    allowed_domains = ["sopharmacy.bg"]
    start_urls = ["https://sopharmacy.bg/bg/mapbox/contactus.json"]

    def parse(self, response):
        for store in response.json()["contact-map"]["features"]:
            item = {
                "ref": store["id"],
                "branch": store["properties"]["name"],
                "street_address": store["properties"]["address"].strip(),
                "city": store["properties"]["city"],
                "lat": store["geometry"]["coordinates"][1],
                "lon": store["geometry"]["coordinates"][0],
                "phone": store["properties"]["contacts"]["phone"],
                "email": store["properties"]["contacts"]["email"],
            }
            item["opening_hours"] = OpeningHours()
            for day in store["properties"]["worktime"]:
                item["opening_hours"].add_ranges_from_string(day, DAYS_BG)
            yield Feature(**item)
