# -*- coding: utf-8 -*-
import json
import re
import scrapy
from scrapy.selector import Selector

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class WalgreensSpider(scrapy.Spider):

    name = "walgreens"
    allowed_domains = ["www.walgreens.com"]
    download_delay = 0.1
    start_urls = ("https://www.walgreens.com/Store-Details.xml",)

    def parse_hours(self, days):
        opening_hours = OpeningHours()
        for day in days:
            opening_hours.add_range(
                day=day["dayOfWeek"][:2],
                open_time=day["opens"],
                close_time=day["closes"],
            )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):

        json_data = json.loads(
            response.xpath('//script[@id="jsonLD"]/text()').extract_first()
        )

        try:
            street_address = json_data["address"]["streetAddress"]
        except KeyError:
            return  # invalid store

        store_id = re.search(r"id=(.*)", response.url).groups()[0]

        store_name = response.xpath(
            '//div[contains(@class, "wag-storedetails-info")]/p/text()'
        ).extract()
        store_name = "".join(store_name)
        store_name = store_name.replace("\xa0", " ")

        props = {
            "name": store_name,
            "addr_full": street_address,
            "city": json_data["address"]["addressLocality"],
            "state": json_data["address"]["addressRegion"],
            "postcode": json_data["address"]["postalCode"],
            "country": json_data["address"]["addressCountry"],
            "phone": json_data["telephone"],
            "ref": store_id,
            "website": response.url,
            "opening_hours": self.parse_hours(json_data["openingHoursSpecification"]),
            "lat": float(json_data["geo"]["latitude"]),
            "lon": float(json_data["geo"]["longitude"]),
            "brand": json_data.get("name")
            or ("Duane Reade" if "duane" in response.url else "Walgreens"),
        }
        return GeojsonPointItem(**props)

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
