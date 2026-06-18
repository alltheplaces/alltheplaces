import pycountry
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class StasherSpider(Spider):
    name = "stasher"
    item_attributes = {"brand": "Stasher"}
    start_urls = ["https://api.stasher.com/v3/stashpoints?page=1&per_page=1000"]

    def start_requests(self):
        yield JsonRequest(url=self.start_urls[0], callback=self.parse)

    def parse(self, response, **kwargs):
        data = response.json()
        for location in data["items"]:
            if location.get("deactivated_at"):
                continue
            item = Feature()
            item["ref"] = location["id"]
            item["name"] = location.get("business_name") or location.get("name")
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")
            item["addr_full"] = location.get("address")
            item["postcode"] = location.get("postal_code")

            country_alpha3 = location.get("country_code", "")
            if country_alpha3:
                try:
                    country = pycountry.countries.get(alpha_3=country_alpha3)
                    if country:
                        item["country"] = country.alpha_2
                except Exception:
                    pass

            oh = OpeningHours()
            if location.get("open_twentyfour_seven"):
                oh.add_days_range(DAYS, "00:00", "23:59")
            else:
                for rule in location.get("opening_hours", []):
                    # day 0 = Monday in Stasher API
                    day = DAYS[rule["day"]]
                    oh.add_range(day=day, open_time=rule["open"], close_time=rule["close"], time_format="%H:%M:%S")
            item["opening_hours"] = oh

            item["extras"]["amenity"] = "left_luggage"
            yield item

        page = data.get("page", 1)
        pages = data.get("pages", 1)
        if page < pages:
            next_page = page + 1
            yield JsonRequest(
                url=f"https://api.stasher.com/v3/stashpoints?page={next_page}&per_page=1000",
                callback=self.parse,
            )
