import json
import re

import scrapy

from locations import hours
from locations.items import Feature


def parse_opening_hours(opening_hours):
    p = re.compile(r"^([A-Za-z-,]+)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$")
    oh = hours.OpeningHours()
    for part in opening_hours:
        m = p.match(part)
        if m:
            (days, open_time, close_time) = m.groups()
            days_split = [d.split("-") for d in days.split(",")]
            for d in days_split:
                if len(d) > 1:
                    oh.add_days_range(hours.day_range(d[0], d[1]), open_time, close_time)
                else:
                    oh.add_range(d[0], open_time, close_time)
        else:
            raise Exception(f"No regex match for opening hours: {part}")
    return oh.as_opening_hours()


class TegutDESpider(scrapy.Spider):
    name = "tegut_de"
    item_attributes = {"brand": "tegut…", "brand_wikidata": "Q1547993"}
    allowed_domains = ["www.tegut.com"]
    start_urls = [
        "https://www.tegut.com/maerkte/marktsuche.html?mktegut%5Baddress%5D=Stuttgart&mktegut%5Bradius%5D=2000&mktegut%5Bsubmit%5D=Markt+suchen"
    ]

    def parse_data(self, response):
        data = response.xpath('//script[@type="application/ld+json"]/text()').get()
        data = data.replace("\n", "")
        store = json.loads(data)

        storeid = store.get("@id", None)
        if storeid:
            properties = {
                "ref": storeid,
                "name": store["name"],
                "street": store["address"]["streetAddress"],
                "city": store["address"]["addressLocality"],
                "postcode": store["address"]["postalCode"],
                "country": store["address"]["addressCountry"],
                "lat": store["geo"]["latitude"],
                "lon": store["geo"]["longitude"],
                "phone": store["telephone"],
                "opening_hours": parse_opening_hours(store["openingHours"]),
                "website": store["url"],
            }

            yield Feature(**properties)

    def parse(self, response):
        stores = response.xpath('//h2[@class="h3 font-weight-bold store_title"]//a/@href').getall()
        for store in stores:
            yield scrapy.Request(f"https://www.tegut.com{store}", callback=self.parse_data)

        for link in response.xpath('//li[@class="list-inline-item"]//a'):
            next = link.xpath("./text()").get().strip()
            if next == ">":
                next_link = link.xpath("./@href").get()
                yield scrapy.Request(f"https://www.tegut.com{next_link}", callback=self.parse)
