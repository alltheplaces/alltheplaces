# -*- coding: utf-8 -*-
import json
import urllib.parse

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class PrimarkSpider(scrapy.Spider):
    name = "primark"
    item_attributes = {"brand": "Primark", "brand_wikidata": "Q137023"}
    allowed_domains = ["primark.com"]
    start_urls = ("https://stores.primark.com/",)

    def parse(self, response):
        for href in response.xpath(
            '(//a[@data-ya-track="directorylink"]|//a[@data-ya-track="businessname"])/@href'
        ).extract():
            url = response.urljoin(href)
            path = urllib.parse.urlparse(url).path
            if path.count("/") == 3:
                yield scrapy.Request(response.urljoin(href), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(href))

    def parse_store(self, response):
        json_text = response.xpath('//script[@class="js-map-config"]/text()').get()
        if json_text is None:
            # These stores are "opening soon"
            return
        js = json.loads(json_text)["entities"][0]["profile"]

        opening_hours = OpeningHours()
        for row in js["hours"]["normalHours"]:
            day = row["day"][:2].capitalize()
            for interval in row["intervals"]:
                start_time = "{:02}:{:02}".format(*divmod(interval["start"], 100))
                end_time = "{:02}:{:02}".format(*divmod(interval["end"], 100))
                opening_hours.add_range(day, start_time, end_time)

        properties = {
            "name": js["name"],
            "addr_full": js["address"]["line1"],
            "ref": js["meta"]["id"],
            "website": response.url,
            "city": js["address"]["city"],
            "state": js["address"]["region"],
            "postcode": js["address"]["postalCode"],
            "country": js["address"]["countryCode"],
            "opening_hours": opening_hours.as_opening_hours(),
            "phone": js["mainPhone"]["number"],
            "lat": response.xpath('//meta[@itemprop="latitude"]/@content').get(),
            "lon": response.xpath('//meta[@itemprop="longitude"]/@content').get(),
        }
        yield GeojsonPointItem(**properties)
