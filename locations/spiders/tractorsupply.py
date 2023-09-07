import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.searchable_points import open_searchable_points

DAYS_NAME = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class TractorSupplySpider(scrapy.Spider):
    name = "tractorsupply"
    item_attributes = {"brand": "Tractor Supply", "brand_wikidata": "Q15109925"}
    allowed_domains = ["tractorsupply.com"]
    download_delay = 1.5
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    }

    def start_requests(self):
        base_url = "https://www.tractorsupply.com/wcs/resources/store/10151/zipcode/fetchstoredetails?responseFormat=json&latitude={lat}&longitude={lng}"

        with open_searchable_points("us_centroids_25mile_radius.csv") as points:
            for point in points:
                _, lat, lon = point.strip().split(",")
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, callback=self.parse)

    def parse_hours(self, hours):
        day_hour = hours.split("|")

        opening_hours = OpeningHours()

        for dh in day_hour:
            try:
                day = DAYS_NAME[dh.split("=")[0]]
                hr = dh.split("=")[1]
                open_time, close_time = hr.split("-")
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
