# -*- coding: utf-8 -*-
import json
import re
import zlib

import scrapy

from scrapy import Selector
from locations.items import GeojsonPointItem
from urllib.parse import urlencode


class SearsSpider(scrapy.Spider):
    name = "sears"
    item_attributes = {"brand": "Sears", "brand_wikidata": "Q6499202"}
    allowed_domains = [
        "www.sears.com",
    ]
    download_delay = 0.3

    def start_requests(self):
        sears_url = "https://www.sears.com/Sitemap_Local.xml.gz"

        yield scrapy.Request(sears_url, callback=self.parse_sears)

    def parse_sears(self, response):
        decompressed_xml = zlib.decompress(response.body, 16 + zlib.MAX_WBITS)
        sel = Selector(text=decompressed_xml)
        for url in sel.xpath("//loc/text()").extract():
            if url.count("/") == 6:
                yield scrapy.Request(url.strip(), callback=self.parse_sears_store)

    def parse_sears_store(self, response):
        # Handle redirects to closed store page, majority are regular store detail pages
        if response.request.meta.get("redirect_urls"):
            if "store-closed" in response.url:
                pass
        else:
            store_script_data = response.xpath(
                '//script[contains(text(),"var storeTitle")]/text()'
            ).extract_first()
            lat = re.search(r"lat = ([0-9.]*),", store_script_data).group(1)
            lon = re.search(r"lon = ([0-9.-]*),", store_script_data).group(1)
            ref = re.search(r'unitNumber = "([0-9]*)",', store_script_data).group(1)

            properties = {
                "ref": ref,
                "name": response.xpath(
                    'normalize-space(//*[@itemprop="name"]//text())'
                ).extract_first(),
                "addr_full": response.xpath(
                    'normalize-space(//span[@itemprop="streetAddress"]//text())'
                ).extract_first(),
                "city": response.xpath(
                    'normalize-space(//span[@itemprop="addressLocality"]//text())'
                ).extract_first(),
                "state": response.xpath(
                    'normalize-space(//span[@itemprop="addressRegion"]//text())'
                ).extract_first(),
                "postcode": response.xpath(
                    'normalize-space(//span[@itemprop="postalCode"]//text())'
                ).extract_first(),
                "phone": response.xpath(
                    'normalize-space(//span[@itemprop="telephone"]//text())'
                ).extract_first(),
                "website": response.url,
                "lat": lat,
                "lon": lon,
            }

            yield GeojsonPointItem(**properties)
