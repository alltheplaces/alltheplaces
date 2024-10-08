import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAYS = [
    "Sun",
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
]
DAY_IDX = {day: idx for idx, day in enumerate(DAYS)}


class DutchBrosSpider(scrapy.Spider):
    name = "dutch_bros"
    item_attributes = {"brand": "Dutch Bros. Coffee", "brand_wikidata": "Q5317253"}

    allowed_domains = ["www.dutchbros.com"]
    start_urls = ("https://files.dutchbros.com/api-cache/stands.json",)

    def parse(self, response):
        for store in response.json():
            # stand not open yet
            if store["future_stand"]:
                continue

            item = Feature(
                ref=store["store_number"],
                name=store["store_nickname"],
                lat=store["lat"],
                lon=store["lon"],
                street_address=store["stand_address"],
                city=store["city"],
                state=store["state"],
                postcode=store["zip_code"],
                website=f'https://locations.dutchbros.com/dutch-bros-coffee-{store["yext_url"]}',
                opening_hours=self.parse_hours(store["hours"]),
            )

            yield item

    def parse_hours(self, hrs):
        o = OpeningHours()
        for hrange in hrs.split(","):
            days, hours = hrange.split(":", 1)
            days, hours = days.strip(), hours.strip()
            try:
                sday, eday = days.split("-", 1)
            except ValueError:
                sday, eday = days, days

            try:
                shour, ehour = hours.split("-", 1)
                if ":" not in shour:
                    shour = shour[:2] + ":00" + shour[2:]
                if ":" not in ehour:
                    ehour = ehour[:2] + ":00" + ehour[2:]
            except ValueError:
                if hours == "Closed":
                    continue
                elif hours == "24hrs":
                    shour, ehour = "12:00am", "11:59pm"
                else:
                    raise

            for idx in range(DAY_IDX[sday], DAY_IDX[eday] + 1):
                o.add_range(DAYS[idx][:2], shour, ehour, "%I:%M%p")
        return o.as_opening_hours()
