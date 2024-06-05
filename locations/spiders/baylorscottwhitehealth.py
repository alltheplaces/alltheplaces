import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BaylorScottWhiteHealthSpider(scrapy.Spider):
    name = "baylorscottwhite"
    item_attributes = {"brand": "Baylor Scott & White Health", "brand_wikidata": "Q41568258"}
    allowed_domains = ["phyndapi.bswapi.com"]
    base_url = "https://phyndapi.bswapi.com/V4/Places/GetLocations"

    def start_requests(self):
        yield scrapy.Request(
            self.base_url + "?perPage=1",
            callback=self.get_pages,
        )

    def get_pages(self, response):
        total_count = response.json()["locationCount"]
        page_number = 0
        page_size = 100

        while page_number * page_size < total_count:
            yield scrapy.Request(self.base_url + f"?perPage={page_size}&pageNumber={page_number + 1}")
            page_number += 1

    def parse(self, response):
        ldata = response.json()["locationResults"]

        for row in ldata:
            properties = {
                "ref": row["locationID"],
                "name": row["locationName"],
                "street_address": clean_address([row["locationStreet1"], row.get("locationStreet2", "")]),
                "city": row["locationCity"],
                "postcode": row["locationZip"],
                "state": row["locationState"],
                "lat": row["coordinates"]["lat"],
                "lon": row["coordinates"]["lon"],
                "phone": row["locationPhone"].replace(".", " "),
                "website": row["locationUrl"],
                "image": row["photoUrl"],
            }

            oh = OpeningHours()
            for day in row["dailyHours"]:
                oh.add_range(
                    day["weekDayName"][:2],
                    day["openingTime"],
                    day["closingTime"],
                    "%H:%M:%S",
                )

            properties["opening_hours"] = oh.as_opening_hours()

            yield Feature(**properties)
