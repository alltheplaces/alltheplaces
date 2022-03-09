# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

DAYS = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Friday": "Fr",
    "Thursday": "Th",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class SunLoanSpider(scrapy.Spider):
    name = "sunloan"
    item_attributes = {"brand": "Sun Loan"}
    allowed_domains = ["sunloan.com"]
    start_urls = ("https://www.sunloan.com/locations/",)
    download_delay = 0.5

    def parse(self, response):
        urls = response.xpath(
            '//div[@id="custom-locations-2"]//div[@class="location-box"]/div/p/strong/a/@href'
        ).extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        try:
            data = response.xpath(
                '//script[contains(text(),"latitude")]/text()'
            ).extract_first()
            data = json.loads(data)
        except TypeError:
            return
        except json.JSONDecodeError:
            data = data.replace('"hasMap": \r\n', "")
            data = json.loads(data)
        if not data:
            return

        properties = {
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
            "website": response.url,
            "ref": response.url,
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": "US",
            "name": data["name"],
        }

        try:
            hours = data["openingHours"]
            if hours:
                properties["opening_hours"] = hours
        except:
            pass

        yield GeojsonPointItem(**properties)

        # yield GeojsonPointItem(
        #     lat=float(data['geo']['latitude']),
        #     lon=float(data['geo']['longitude']),
        #     website=response.url,
        #     ref=response.url,
        #     #opening_hours=data['openingHours'],
        #     addr_full=data['address']['streetAddress'],
        #     city=data['address']['addressLocality'],
        #     state=data['address']['addressRegion'],
        #     postcode=data['address']['postalCode'],
        #     country='US',
        #     name=data['name'],
        # )
