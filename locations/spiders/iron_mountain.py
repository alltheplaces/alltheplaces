# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class IronMountainSpider(scrapy.Spider):
    name = "iron_mountain"
    start_urls = ("https://locations.ironmountain.com/",)

    def parse(self, response):
        urls = response.xpath(
            '//*[@id="browse-expand"]/div/div[1]/div/li/div/a/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(
                url=url, callback=self.parse_list, meta={"country": "USA"}
            )
        urls = response.xpath(
            '//*[@id="browse-expand"]/div/div[2]/div/li/div/a/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(
                url=url, callback=self.parse_list, meta={"country": "Canada"}
            )

    def parse_list(self, response):
        urls = response.xpath(
            '//*[@id="main-container"]/div[2]/div[3]/div[1]/div/div[2]/div[2]/ul/li/div/a/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_city,
                meta={"country": response.meta.get("country")},
            )

    def parse_city(self, response):
        urls = response.xpath(
            '//*[@id="main-container"]/div[2]/div[3]/div[1]/div/div[2]/div[2]/ul/li/a/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_location,
                meta={"country": response.meta.get("country")},
            )

    def parse_location(self, response):
        data = re.sub(
            "'", "", response.xpath('//*[@id="gmap"]/script/text()').extract()[0]
        )
        data = data.replace(",}", "}")
        data = data.replace("RLS.defaultData = ", "")
        data = data.replace(";", "")
        address = json.loads(
            "{"
            + str.join(
                ",",
                json.loads(data)["markerData"][0]["info"]
                .replace("</div>", "")
                .split(",")[1:],
            )
        )
        yield GeojsonPointItem(
            addr_full=address["address_1"],
            city=address["city"],
            state=response.xpath(
                '//*[@id="main-container"]/div[2]/div[1]/ol/li[2]/a/text()'
            )
            .extract()[0]
            .strip(" "),
            postcode=address["post_code"],
            lat=float(address["lat"]),
            lon=float(address["lng"]),
            phone=address["local_phone"],
            website=address["url"].replace("\\", ""),
            country=response.meta.get("country"),
            ref=address["url"].replace("\\", ""),
        )
