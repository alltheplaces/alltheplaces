# -*- coding: utf-8 -*-
import scrapy
import re
import time
from scrapy.utils.gz import gunzip

from locations.items import GeojsonPointItem


class PDQSpider(scrapy.Spider):
    name = "pdq"
    item_attributes = {"brand": "PDQ"}
    allowed_domains = ["eatpdq.qatserver.com"]
    start_urls = ("http://eatpdq.qatserver.com/sitemap/sitemap.gz",)

    def parse(self, response):

        sitemap = gunzip(response.body)
        regex = re.compile(r"http://eatpdq.qatserver.com/locations/\S+(?=</loc>)")
        city_urls = re.findall(regex, str(sitemap))

        for path in city_urls:
            if path.strip() == "http://eatpdq.qatserver.com/locations/find-a-location":
                pass
            else:
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):
        if "Sitefinity trial version" in response.xpath("//title/text()").extract():
            yield scrapy.Request(
                response.request.url,
                callback=self.parse_store,
            )
        else:
            if response.xpath('//div[@class="hours"]/div').extract():
                storeHoursHTML = (
                    str(response.xpath('//div[@class="hours"]/div').extract())
                    .replace("'", "")
                    .replace("[", "")
                    .replace("]", "")
                )
                p = re.compile(r"<.*?>")
                storeHours = p.sub("", storeHoursHTML)
                storeHours = storeHours.replace("\\n", " - ")
                storeHours = "".join(storeHours.strip())
            else:
                storeHours = response.xpath('//div[@class="hours"]/div').extract()

            properties = {
                "name": response.xpath(
                    '//div[@class="name"]/h1/text()'
                ).extract_first(),
                "ref": response.xpath('//div[@class="name"]/h1/text()').extract_first(),
                "addr_full": response.xpath('//div[@class="address"]/text()')
                .extract_first()
                .strip(),
                "city": response.xpath('//div[@class="address"]/text()[2]')
                .extract_first()
                .split(",")[0],
                "state": response.xpath('//div[@class="address"]/text()[2]')
                .extract_first()
                .split()[1],
                "postcode": response.xpath('//div[@class="address"]/text()[2]')
                .extract_first()
                .split()[-1],
                "phone": response.xpath("//tel/a[@href]/text()").extract_first(),
                "website": response.request.url,
                "opening_hours": storeHours,
                "lat": float(
                    response.xpath('//div[@class="address"]/a/@href')
                    .extract_first()
                    .split("@")[1]
                    .split(",")[0]
                ),
                "lon": float(
                    response.xpath('//div[@class="address"]/a/@href')
                    .extract_first()
                    .split("@")[1]
                    .split(",")[1]
                ),
            }

            yield GeojsonPointItem(**properties)
