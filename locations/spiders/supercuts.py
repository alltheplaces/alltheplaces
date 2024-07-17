import scrapy

from locations.hours import OpeningHours, day_range
from locations.items import Feature


class SuperCutsSpider(scrapy.Spider):
    name = "supercuts"
    item_attributes = {"brand": "Supercuts", "brand_wikidata": "Q7643239"}
    allowed_domains = ["api-booking.regiscorp.com"]
    start_urls = ["https://www.supercuts.com/salon-directory"]

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "x-api-key": "zcXG3YV70a2u7T9tTK9S7MFMJUUZ66Vawq5qXxnj",
        },
    }

    def start_requests(self):
        yield scrapy.http.JsonRequest(
            "https://api-booking.regiscorp.com/v2/getstatesbybrand",
            data={"siteId": "1"},
            callback=self.parse_index,
        )

    def parse_index(self, response):
        for country in response.json().values():
            for state in country:
                st = state["abbreviation"].lower()
                yield scrapy.http.JsonRequest(
                    "https://api-booking.regiscorp.com/v2/searchbylocation",
                    data={"siteIds": "1", "state": st},
                    callback=self.parse_state,
                )

    def parse_state(self, response):
        for salon in response.json():
            yield scrapy.http.JsonRequest(
                "https://api-booking.regiscorp.com/v1/getsalondetails",
                data={"siteId": "1", "salonId": salon["salonId"]},
                callback=self.parse_salon,
            )

    def parse_salon(self, response):
        data = response.json()["Salon"]
        properties = {
            "lat": data["latitude"],
            "lon": data["longitude"],
            "name": data["name"],
            "addr_full": data["address"],
            "city": data["city"],
            "state": data["state"],
            "postcode": data["zip"],
            "phone": data.get("phonenumber"),
            "website": f'https://www.supercuts.com/checkin/{data["storeID"]}',
            "opening_hours": self.get_hours(data["store_hours"]),
            "ref": data["storeID"],
        }
        yield Feature(**properties)

    @staticmethod
    def get_hours(hours):
        oh = OpeningHours()
        for spec in hours:
            if "-" in spec["days"]:
                start_day, end_day = spec["days"].split(" - ")
                for day in day_range(start_day[:2], end_day[:2]):
                    oh.add_range(day, spec["hours"]["open"], spec["hours"]["close"], "%I:%M %p")
            else:
                day = spec["days"][:2]
                if "" in (spec["hours"]["open"], spec["hours"]["close"]):
                    continue
                oh.add_range(day, spec["hours"]["open"], spec["hours"]["close"], "%I:%M %p")
        return oh.as_opening_hours()
