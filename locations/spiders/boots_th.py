# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from scrapy import Selector


class BootsTHSpider(scrapy.Spider):
    name = "boots_th"
    item_attributes = {"brand": "Boots"}
    allowed_domains = ["www.intl.boots.com"]
    download_delay = 0.5
    start_urls = [
        "http://www.intl.boots.com/storelocator/Results.aspx?country_id=4&s=",
    ]

    def parse(self, response):
        data = response.xpath(
            '//script[@type="text/javascript" and contains(text(), "stores")]/text()'
        ).extract_first()
        stores = json.loads(re.search(r"stores = (.*);", data).group(1))

        for i, store_data in enumerate(stores, start=1):
            store_div_content = Selector(text=store_data[4])
            ref = re.search(
                r"store_id=(.*)$", store_div_content.xpath("//a/@href").extract_first()
            ).group(1)
            website = response.urljoin(
                store_div_content.xpath("//a/@href").extract_first()
            )
            address = response.xpath(
                "normalize-space(//li[{index}]/a/div/text()[2])".format(index=i)
            ).extract_first()
            phone = store_div_content.xpath(
                '//p[@class="telephone"]/text()'
            ).extract_first()

            properties = {
                "name": store_data[0].strip(),
                "ref": ref,
                "addr_full": address,
                "country": "TH",
                "phone": phone,
                "website": website,
                "lat": store_data[1],
                "lon": store_data[2],
            }

            yield GeojsonPointItem(**properties)
