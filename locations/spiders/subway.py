# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

from urllib.parse import urlparse
import json


DAY_MAPPING = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}


class SubwaySpider(scrapy.Spider):
    name = "subway"
    item_attributes = {"name": "Subway", "brand": "Subway", "brand_wikidata": "Q244457"}
    allowed_domains = ["restaurants.subway.com"]
    start_urls = ["https://restaurants.subway.com/"]

    link_extractor = scrapy.linkextractors.LinkExtractor(
        restrict_css=".Directory-listLinks, .Directory-listTeasers"
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(link.url)

        js = response.xpath('//script[@class="js-hours-config"]/text()').get()
        if js:
            yield from self.parse_restaurant(json.loads(js))

    def parse_restaurant(self, js):
        # Note: Of the five different coordinate fields, this is the one that always exists
        lat_long = js["profile"]["yextDisplayCoordinate"]
        website = ""
        if "websiteUrl" in js["profile"]:
            website = urlparse(js["profile"]["websiteUrl"])._replace(query="").geturl()
        properties = {
            "lat": lat_long["lat"],
            "lon": lat_long["long"],
            "ref": js["profile"]["meta"]["id"],
            "addr_full": js["profile"]["address"]["line1"],
            "extras": {
                "addr:unit": js["profile"]["address"]["line2"],
                # Note: line3 is always null
                "loc_name": js["profile"]["address"]["extraDescription"],
            },
            "city": js["profile"]["address"]["city"],
            "state": js["profile"]["address"]["region"],
            "postcode": js["profile"]["address"]["postalCode"],
            "country": js["profile"]["address"]["countryCode"],
            "phone": js["profile"].get("mainPhone", {}).get("number"),
            "opening_hours": self.parse_hours(js["profile"]["hours"]["normalHours"]),
            "website": website,
        }
        yield GeojsonPointItem(**properties)

    def parse_hours(self, hours_json):
        opening_hours = OpeningHours()
        for date in hours_json:
            day = DAY_MAPPING[date["day"]]
            for interval in date["intervals"]:
                start_hr, start_min = divmod(interval["start"], 100)
                end_hr, end_min = divmod(interval["end"], 100)
                opening_hours.add_range(
                    day, f"{start_hr}:{start_min}", f"{end_hr}:{end_min}"
                )
        return opening_hours.as_opening_hours()
