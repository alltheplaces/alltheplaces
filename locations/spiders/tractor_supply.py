import scrapy

from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class TractorSupplySpider(scrapy.Spider):
    name = "tractor_supply"
    item_attributes = {"brand": "Tractor Supply", "brand_wikidata": "Q15109925"}
    allowed_domains = ["tractorsupply.com"]
    download_delay = 1.5
    user_agent = BROWSER_DEFAULT
    custom_settings = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self):
        base_url = "https://www.tractorsupply.com/wcs/resources/store/10151/zipcode/fetchstoredetails?responseFormat=json&latitude={lat}&longitude={lng}"

        for lat, lon in point_locations("us_centroids_25mile_radius.csv"):
            url = base_url.format(lat=lat, lng=lon)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse_hours(self, hours):
        day_hour = hours.split("|")

        opening_hours = OpeningHours()

        for dh in day_hour:
            try:
                dh_left, dh_right = dh.split("=")
                day = dh_left[:2]
                open_time, close_time = dh_right.split("-")
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M %p",
                )
            except Exception:
                continue

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()
        store_data = data["storesList"]

        for store in store_data:
            properties = {
                "ref": store["stlocId"],
                "name": store["storeName"],
                "addr_full": store["addressLine"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zipCode"],
                "phone": store["phoneNumber"],
                "lat": store["latitude"],
                "lon": store["longitude"],
            }

            hours = self.parse_hours(store["storeHours"])
            if hours:
                properties["opening_hours"] = hours

            yield Feature(**properties)
