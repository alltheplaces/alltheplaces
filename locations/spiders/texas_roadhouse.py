import json

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class TexasRoadhouseSpider(scrapy.Spider):
    name = "texas_roadhouse"
    item_attributes = {
        "brand": "Texas Roadhouse",
        "brand_wikidata": "Q7707945",
    }
    allowed_domains = ["www.texasroadhouse.com"]
    start_urls = ("https://www.texasroadhouse.com/sitemap.xml",)
    requires_proxy = True

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for weekday in store_hours:
            # convert day from full Monday to Mo, etc
            day = weekday.get("day")[:2]
            open_time = weekday.get("hours").get("openTime")
            close_time = weekday.get("hours").get("closeTime")
            opening_hours.add_range(
                day=day,
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M%p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        for path in city_urls:
            if path.startswith("https://www.texasroadhouse.com/locations/"):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):
        data = json.loads(response.xpath("//script/text()").extract_first()[22:-1])

        properties = {
            "lat": data["latitude"],
            "lon": data["longitude"],
            "ref": data["url"],
            "name": data["name"],
            "addr_full": data["address1"],
            "city": data["city"],
            "state": data["state"],
            "postcode": data["postalCode"],
            "country": data["countryCode"],
            "phone": data["telephone"],
            "website": response.urljoin(data["url"]),
            "opening_hours": self.parse_hours(data["schedule"]),
        }

        yield Feature(**properties)
