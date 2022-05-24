# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class ThorntonsSpider(scrapy.Spider):
    name = "thorntons"
    item_attributes = {"brand": "Thorntons", "brand_wikidata": "Q683102"}
    allowed_domains = ["www.thorntonsinc.com"]
    start_urls = [
        "https://www.thorntonsinc.com/about-us/location-finder",
    ]
    download_delay = 0.3

    def parse(self, response):
        stores = response.xpath('//div[@data-type="store"]')

        for store in stores:
            store_name = store.xpath(
                './/p/span[@data-type="name"]/text()'
            ).extract_first()
            ref = store_name.split("#")[-1]

            properties = {
                "ref": ref,
                "name": store_name,
                "addr_full": store.xpath(
                    './/p/span[@data-type="address"]/text()'
                ).extract_first(),
                "city": store.xpath(
                    './/p/span[@data-type="city"]/text()'
                ).extract_first(),
                "state": store.xpath(
                    './/p/span[@data-type="state"]/text()'
                ).extract_first(),
                "postcode": store.xpath(
                    './/p/span[@data-type="zip"]/text()'
                ).extract_first(),
                "lat": float(store.xpath(".//@data-latitude").extract_first()),
                "lon": float(store.xpath(".//@data-longitude").extract_first()),
                "phone": store.xpath(
                    './/p/span[@data-type="phone"]/text()'
                ).extract_first(),
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
