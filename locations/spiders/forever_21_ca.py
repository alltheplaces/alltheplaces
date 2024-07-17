import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class Forever21CASpider(scrapy.Spider):
    name = "forever_21_ca"
    item_attributes = {
        "brand": "Forever 21",
        "brand_wikidata": "Q1060537",
    }
    allowed_domains = ["forever21.ca"]
    start_urls = [
        "https://www.forever21.ca/apps/api/v1/stores",
    ]

    def parse(self, response):
        for row in response.json()["stores"]:
            oh = OpeningHours()
            for hour in row["open_hours"]:
                oh.add_range(hour["day"][:2], hour["open_time"], hour["close_time"])
            properties = {
                "ref": row["store_code"],
                "lat": row["address"]["latitude"],
                "lon": row["address"]["longitude"],
                "name": row["address"]["name"],
                "phone": row["phone"],
                "street_address": row["address"]["line1"],
                "city": row["address"]["city"],
                "state": row["address"]["state"],
                "postcode": row["address"]["zip"],
                "country": row["address"]["country"],
                "opening_hours": oh.as_opening_hours(),
            }
            yield Feature(**properties)
