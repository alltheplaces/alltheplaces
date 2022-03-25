# -*- coding: utf-8 -*-
import re

from urllib.parse import unquote_plus

import scrapy

from locations.items import GeojsonPointItem


class XlPartsSpider(scrapy.Spider):
    name = "xl_parts"
    item_attributes = {"brand": "XL Parts"}
    allowed_domains = ["www.xlparts.com"]

    def start_requests(self):
        url = "https://www.xlparts.com/en/locations"

        yield scrapy.http.FormRequest(url=url, method="POST", callback=self.parse)

    def parse(self, response):
        stores = response.xpath('//div[contains(@id, "store")]')
        script_data = response.xpath(
            '//script[contains(text(), "var map")]'
        ).extract_first()

        for store in stores:
            store_div = store.xpath("./@id").extract_first()
            ref = re.search(r"store_div_([0-9]*)", store_div).group(1)
            name = store.xpath("./h3/text()").extract_first().strip()
            addr_url = store.xpath("./ul/li/a/@href").extract_first()
            addr_full = unquote_plus(re.search(r"dir//(.*)", addr_url).group(1))
            addr_full = " ".join(addr_full.split())
            phone = store.xpath("./ul/li/span/text()").extract_first()

            # Fetch the coordinates
            pattern = f"""data\['storeID'\] \= "{store_div}"\;.*?var lat\=([0-9.]*);.*?var longtd=([0-9.-]*);"""
            lat, lon = re.search(
                pattern, script_data, flags=re.MULTILINE | re.DOTALL
            ).groups()

            properties = {
                "ref": ref,
                "name": name,
                "addr_full": addr_full,
                "lat": lat,
                "lon": lon,
                "phone": phone,
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
