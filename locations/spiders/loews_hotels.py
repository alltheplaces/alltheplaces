# -*- coding: utf-8 -*-
import re
import json

import scrapy

from locations.items import GeojsonPointItem


class LoewsHotelsSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "loews"
    item_attributes = {"brand": "Loews Hotels", "brand_wikidata": "Q6666622"}
    allowed_domains = ["loewshotels.com"]
    start_urls = ("https://www.loewshotels.com/destinations",)

    def parse(self, response):
        urls = response.xpath('//div[@class="row"]//p//a/@href').extract()
        x = "/omni-partnership"
        for url in urls:
            if url.startswith("/booking"):
                pass
            elif "omni" in url:
                pass
            elif "hotel-1000" in url:
                pass
            elif "policy" in url:
                pass
            elif "mokara" in url:
                pass
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_loc)

    def parse_loc(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "address")]/text()'
            ).extract_first()
        )
        try:
            properties = {
                "ref": data["name"],
                "name": data["name"],
                "addr_full": response.xpath('//span[@class="street-address"]/text()')[0]
                .extract()
                .strip("]["),
                "city": data["address"]["addressLocality"],
                "state": data["address"]["addressRegion"],
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["addressCountry"],
                "phone": data.get("telephone"),
                "lat": float(data["geo"]["latitude"]),
                "lon": float(data["geo"]["longitude"]),
            }

            yield GeojsonPointItem(**properties)
        except:
            properties = {
                "ref": data["name"],
                "name": data["name"],
                "addr_full": response.xpath('//span[@class="street-address"]/text()')
                .extract()[0]
                .strip("]["),
                "city": data["address"]["addressLocality"],
                "state": data["address"]["addressRegion"],
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["addressCountry"],
                "phone": data.get("telephone"),
            }

            yield GeojsonPointItem(**properties)
