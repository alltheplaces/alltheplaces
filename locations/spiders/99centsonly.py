import json
import scrapy
import re
from scrapy.selector import Selector

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class NinetyNineCentsOnlySpider(scrapy.Spider):
    name = "99centsonly"
    item_attributes = {"brand": "99 Cents Only Stores", "brand_wikidata": "Q4646294"}
    allowed_domains = ["99only.com"]

    start_urls = [
        "https://99only.com/sitemap.xml",
    ]

    def parse_hours(self, days, hours):
        opening_hours = OpeningHours()

        for d, h in zip(days, hours):
            if d == "Today":
                # two days before the day after tomorrow
                d = DAY_MAPPING[DAY_MAPPING.index(days[days.index("Tomorrow") + 1]) - 2]
            elif d == "Tomorrow":
                # one day before the day after tomorrow
                d = DAY_MAPPING[DAY_MAPPING.index(days[days.index("Tomorrow") + 1]) - 1]

            open_time, close_time = h.split(" to ")
            opening_hours.add_range(
                day=d[:2],
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M %p",
            )

        return opening_hours.as_opening_hours()

    def parse_location(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract_first()
        data = json.loads(data)["@graph"][0]

        properties = {
            "ref": response.xpath('//span[@class="store-number"]/text()')
            .extract_first()
            .strip("#"),
            "name": response.xpath(
                '//div[@class="store-splash"]/h1/span/text()'
            ).extract_first(),
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "website": response.url,
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
        }

        hours = self.parse_hours(
            days=response.xpath(
                '//div[@class="store-hours-list"]//td[@class="day"]/text()'
            ).extract(),
            hours=response.xpath(
                '//div[@class="store-hours-list"]//td[@class="hours"]/text()'
            ).extract(),
        )
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()

        for url in urls:
            if re.match(r"^https://99only.com/stores/.+?$", url):
                if "near-me" in url:
                    continue
                yield scrapy.Request(url, callback=self.parse_location)
