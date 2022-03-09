# -*- coding: utf-8 -*-
import re
import json

import scrapy

from locations.items import GeojsonPointItem


class GoodYearSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "goodyear"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    allowed_domains = ["goodyear.com"]
    start_urls = ("https://www.goodyear.com/en-US/tires/tire-shop",)

    def parse(self, response):
        urls = response.xpath('//ul[@id="hiddenRegions"]//a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        stateurls = response.xpath(
            '//div[@class="sub-group col-lg-4"]//a/@href'
        ).extract()
        for stateurl in stateurls:
            yield scrapy.Request(response.urljoin(stateurl), callback=self.parse_city)

    def parse_city(self, response):
        cityurls = response.xpath('//div[@class="item-container "]/a/@href').extract()
        for cityurl in cityurls:
            yield scrapy.Request(
                response.urljoin(cityurl), callback=self.parse_location
            )

    def parse_location(self, response):
        store_js = response.xpath(
            '//script[@type="text/javascript" and contains(text(), "formattedAddress")]/text()'
        ).extract()
        storetext = store_js[0]
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )
        json_prelim_data = re.search("name(.*)", storetext).group()
        json_data = json_prelim_data.split(",")
        lat = 0.0
        lon = 0.0
        if json_data[5].startswith('"lati'):
            lat = float(json_data[5].replace('"latitude":', ""))
            lon = float(json_data[6].replace('"longitude":', ""))
        elif json_data[6].startswith('"lati'):
            lat = float(json_data[6].replace('"latitude":', ""))
            lon = float(json_data[7].replace('"longitude":', ""))
        else:
            for i in json_data:
                if i.startswith('"lati'):
                    lat = float(i.replace('"latitude":', ""))
                elif i.startswith('"longit'):
                    lon = float(i.replace('"longitude":', ""))

        properties = {
            "ref": (json_data[0].replace('name":', "").strip('"')),
            "name": data["description"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data.get("telephone"),
            "lat": lat,
            "lon": lon,
        }

        yield GeojsonPointItem(**properties)
