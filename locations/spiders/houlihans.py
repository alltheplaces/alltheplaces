# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class HoulihansSpider(scrapy.Spider):
    name = "houlihans"
    item_attributes = {"brand": "Houlihan's"}
    allowed_domains = ["houlihans.com"]
    start_urls = ("http://www.houlihans.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        regex = re.compile(r"http(s://|://www.)houlihans.com/my-houlihans/\S+")
        for path in city_urls:
            if re.search(regex, path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )
            else:
                pass

    def parse_store(self, response):

        regex = re.compile(r"http(s://|://www.)houlihans.com/my-houlihans/\S+")
        if re.search(regex, response.request.url):
            properties = {
                "name": response.xpath(
                    '//span[@itemprop="name"]/text()'
                ).extract_first(),
                "ref": response.xpath(
                    '//span[@itemprop="name"]/text()'
                ).extract_first(),
                "addr_full": response.xpath(
                    '//span[@itemprop="streetAddress"]/text()'
                ).extract_first(),
                "city": response.xpath(
                    '//span[@itemprop="addressLocality"]/text()'
                ).extract_first(),
                "state": response.xpath(
                    '//span[@itemprop="addressRegion"]/text()'
                ).extract_first(),
                "postcode": response.xpath(
                    '//span[@itemprop="postalCode"]/text()'
                ).extract_first(),
                "phone": response.xpath(
                    '//span[@itemprop="telephone"]/a/text()'
                ).extract_first(),
                "website": response.request.url,
                "opening_hours": " ".join(
                    str(
                        response.xpath(
                            '//div[@id="header"]/div/div/div/div/div[@class="location-hours"]/p/span/text()'
                        ).extract()
                    )
                    .replace("\\r", "")
                    .replace(",", " -")
                    .split()
                )
                .replace("[", "")
                .replace("]", "")
                .replace("'", ""),
                "lat": float(
                    response.xpath('//div/div[@class="location-actions"]/a[@href]')
                    .extract_first()
                    .split("q=")[1]
                    .split("%")[0]
                    .split(",")[0]
                ),
                "lon": float(
                    response.xpath('//div/div[@class="location-actions"]/a[@href]')
                    .extract_first()
                    .split("q=")[1]
                    .split("%")[0]
                    .split(",")[1]
                ),
            }

            yield GeojsonPointItem(**properties)

        else:
            pass
