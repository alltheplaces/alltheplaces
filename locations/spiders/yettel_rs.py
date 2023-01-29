import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class YettelRSSpider(scrapy.Spider):
    name = "yettel_rs"
    item_attributes = {
        "brand": "Yettel",
        "brand_wikidata": "Q1780171",
        "country": "RS",
    }

    def start_requests(self):
        url = "https://www.yettel.rs/stores/latlong/"
        yield scrapy.http.FormRequest(url=url, formdata={"lat": "0", "lng": "0", "dist": "10000000000"}, method="POST")

    def parse(self, response):
        for index, store in enumerate(response.json()["data"]["stores"]):
            item = Feature()
            item["ref"] = store["id"]

            item["lat"] = store["lat"]
            item["lon"] = store["lng"]

            item["city"] = store["city"]
            item["postcode"] = store["post_number"]
            item["street_address"] = store["address"]

            oh = OpeningHours()

            for wh in store["workingHoursFormated"]:
                if wh["day"] == "Ponedeljak":
                    oh.add_range("Mo", wh["startTime"], wh["endTime"])
                if wh["day"] == "Utorak":
                    oh.add_range("Tu", wh["startTime"], wh["endTime"])
                if wh["day"] == "Sreda":
                    oh.add_range("We", wh["startTime"], wh["endTime"])
                if wh["day"] == "Četvrtak":
                    oh.add_range("Th", wh["startTime"], wh["endTime"])
                if wh["day"] == "Petak":
                    oh.add_range("Fr", wh["startTime"], wh["endTime"])
                if wh["day"] == "Subota":
                    oh.add_range("Sa", wh["startTime"], wh["endTime"])
                if wh["day"] == "Nedelja":
                    oh.add_range("Su", wh["startTime"], wh["endTime"])

            item["opening_hours"] = oh
            yield item
