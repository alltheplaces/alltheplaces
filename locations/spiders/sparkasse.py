import scrapy
import json
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SparkasseSpider(scrapy.Spider):
    name = "sparkasse"
    allowed_domains = ["www.sparkasse.de"]
    download_delay = 2

    def start_requests(self):
        for c in "abcdefghijklmnopqrstuvwxyz":
            url = "https://www.sparkasse.de/filialen/{}.html".format(c)

            yield scrapy.http.FormRequest(url=url, callback=self.parse)

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in store_hours:
            day = time = open_time = close_time = ""
            try:
                (day, time) = store_day.split()
            except ValueError as e:
                print("Error in store_day: {}".format(store_day))

            if time:
                (open_time, close_time) = time.split("-")
                open_time = open_time.replace("24:00", "00:00")
                close_time = close_time.replace("24:00", "00:00")

            if open_time is None and close_time is None:
                continue
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse_details(self, response):
        json_data = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).getall()
        if json_data:
            json_data = json_data[0]
        store = json.loads(json_data)
        store = store[0]
        properties = {
            "lat": store["geo"].get("latitude"),
            "lon": store["geo"].get("longitude "),
            "name": store.get("name"),
            "street": store["address"].get("streetAddress"),
            "city": store["address"].get("addressLocality"),
            "postcode": store["address"].get("postalCode"),
            "phone": store.get("telephone"),
            "ref": response.meta.get("url"),
            "extras": {
                "image": store.get("image"),
                "fax": store.get("faxNumber"),
                "email": store.get("email"),
                "url": response.meta.get("url"),
            },
        }
        hours = self.parse_hours(store.get("openingHours"))

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        links = re.findall(
            r'<a class="object-link grey-link" href="(.+?)">', response.text
        )
        if links:
            for l in links:
                url = "https://www.sparkasse.de/filialen/{}".format(l)
                yield scrapy.Request(
                    url=url, callback=self.parse_details, meta={"url": url}
                )
