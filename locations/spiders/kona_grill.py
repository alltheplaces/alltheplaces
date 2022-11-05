import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class KonaGrillSpider(scrapy.Spider):
    download_delay = 0.2
    name = "konagrill"
    item_attributes = {
        "brand": "Kona Grill",
        "brand_wikidata": "Q6428706",
        "country": "US",
    }
    allowed_domains = ["konagrill.com"]
    start_urls = ["https://www.konagrill.com/ajax/getalllocations"]

    def parse(self, response):
        store_data = response.json()

        # Get store details
        for store in store_data.get("data", {}).values():
            yield scrapy.http.FormRequest(
                url="https://www.konagrill.com/ajax/getlocationdetails",
                formdata={"id": store["id"]},
                callback=self.parse_store,
            )

    def parse_store(self, response):
        response_data = response.json()
        if not response_data.get("data"):
            return

        store = response_data.get("data")
        dh = store.get("dininghours")
        # Data is inconsistent some keys were found with a trailing space
        opening_hours = self.parse_hours(
            dh.get("dining hours") or dh.get("dining hours ")
        )
        properties = {
            "street_address": store.get("address"),
            "city": store.get("city"),
            "email": store.get("email"),
            "lat": store.get("latitude"),
            "lon": store.get("longitude"),
            "name": store.get("title"),
            "opening_hours": opening_hours,
            "phone": store.get("phone_number"),
            "postcode": store.get("zip"),
            "ref": store.get("id"),
            "state": store.get("state"),
            "website": store.get("order_online_url"),
        }

        yield GeojsonPointItem(**properties)

    def parse_hours(self, hours):
        oh = OpeningHours()

        for t in hours:
            # Some day entries contain invalid week data, e.g. "Brunch"
            # "Brunch" is a special dining hour that is contained in regular hours, ignore it
            if "Brunch" in t.get("days"):
                continue
            days = self.parse_days(t.get("days"))
            open_time, close_time = t.get("hours").replace("*", "").split("-")
            ot = open_time.strip()
            ct = close_time.strip()
            for day in days:
                oh.add_range(day=day, open_time=ot, close_time=ct, time_format="%I%p")

        return oh.as_opening_hours()

    def parse_days(self, days):
        """Parse day ranges and returns a list of days it represent
        The following formats are considered:
          - Single day, e.g. "Mon", "Monday"
          - Range, e.g. "Mon-Fri", "Tue-Sund", "Sat-Sunday"
          - Two days, e.g. "Sat & Sun", "Friday & Su"

        Returns a list with the weekdays
        """
        parsed_days = []

        # Range
        # Produce a list of weekdays between two days e.g. su-sa, mo-th, etc.
        if "-" in days:
            d = days.split("-")
            r = [i.strip()[:2] for i in d]
            s = WEEKDAYS.index(r[0].title())
            e = WEEKDAYS.index(r[1].title())
            if s <= e:
                return WEEKDAYS[s : e + 1]
            else:
                return WEEKDAYS[s:] + WEEKDAYS[: e + 1]
        # Two days
        if "&" in days:
            d = days.split("&")
            return [i.strip()[:2].title() for i in d]
        # Single days
        else:
            return [days.strip()[:2].title()]
