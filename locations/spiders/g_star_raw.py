import re

import scrapy

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class GStarRawSpider(scrapy.Spider):
    name = "g_star_raw"
    item_attributes = {"brand": "G-Star Raw", "brand_wikidata": "Q1484081"}
    allowed_domains = ["g-star.com"]
    start_urls = ["https://www.g-star.com/en_us/find-a-store/g-star-raw-brand-store"]

    def parse(self, response):
        countries = response.xpath('//script[@class="localeSelector-country-options"]').get()
        countries = re.findall(r'value="[a-z]{2}"', countries)
        for country in countries:
            url = f"https://www.g-star.com/en_us/find-a-store/getstores?country_iso={country[7:9].upper()}&output_details=1"
            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        for data in response.json().get("results"):
            if "Mono" in data.get("storeFinderCategory"):
                item = Feature()
                item["ref"] = data.get("storeId")
                item["name"] = data.get("name")
                item["phone"] = data.get("telephoneNumber")
                item["street_address"] = data.get("address", {}).get("streetname")
                item["city"] = data.get("address", {}).get("city")
                item["state"] = data.get("address", {}).get("state")
                item["postcode"] = data.get("address", {}).get("postalCode")
                item["country"] = data.get("address", {}).get("country")
                item["lat"] = data.get("latitude")
                item["lon"] = data.get("longitude")
                item["website"] = (
                    f'https://www.g-star.com{data.get("contentPageUrl")}' if data.get("contentPageUrl") else None
                )
                oh = OpeningHours()
                for day in DAYS_FULL:
                    if data.get(day.lower()) != "Closed" and None:
                        return
                    oh.add_range(
                        day=day.lower(),
                        open_time=data.get(day.lower()).split(" - ")[0],
                        close_time=data.get(day.lower()).split(" - ")[0],
                        time_format=(
                            "%I:%M %p" if "PM" in data.get(day.lower()) or "AM" in data.get(day.lower()) else "%H:%M"
                        ),
                    )

                item["opening_hours"] = oh.as_opening_hours()

                yield item
