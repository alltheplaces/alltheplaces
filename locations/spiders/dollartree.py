# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class DollarTreeSpider(scrapy.Spider):
    name = "dollartree"
    item_attributes = {"brand": "Dollar Tree", "brand_wikidata": "Q5289230"}
    allowed_domains = ["dollartree.com"]
    start_urls = ("https://www.dollartree.com/locations",)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            try:
                opening_hours.add_range(
                    day=hour["dayOfWeek"][0][:2],
                    open_time=hour["opens"],
                    close_time=hour["closes"],
                )
            except:
                continue  # closed or no time range given

        return opening_hours.as_opening_hours()

    def address(self, address):
        if not address:
            return None

        addr_tags = {
            "addr_full": address["streetAddress"],
            "city": address["addressLocality"],
            "state": address["addressRegion"],
            "postcode": address["postalCode"],
            "country": address["addressCountry"],
        }

        return addr_tags

    def parse(self, response):
        urls = response.xpath("///div[2]/table//@href")
        for path in urls:
            yield scrapy.Request(response.urljoin(path.extract()))

        store_urls = response.xpath('//*[contains(@class, "storeinfo_div")]/a//@href')
        if store_urls:
            for store_url in store_urls:
                yield scrapy.Request(
                    response.urljoin(store_url.extract()), callback=self.parse_store
                )

    def parse_store(self, response):
        json_data = response.xpath('//head/script[@type="application/ld+json"]/text()')[
            1
        ].extract()
        json_data = json_data.replace(
            "// if the location file does not have the hours separated into open/close for each day, remove the below section",
            "",
        )
        data = json.loads(json_data)

        properties = {
            "name": data.get("containedIn"),
            "phone": data["telephone"],
            "website": response.xpath('//head/link[@rel="canonical"]/@href')[
                0
            ].extract(),
            "ref": data["@id"],
            "opening_hours": self.parse_hours(data["openingHoursSpecification"]),
            "lon": float(data["geo"]["longitude"]),
            "lat": float(data["geo"]["latitude"]),
            "brand": data["branchOf"]["name"],
        }

        address = self.address(data["address"])
        if address:
            properties.update(address)

        yield GeojsonPointItem(**properties)
