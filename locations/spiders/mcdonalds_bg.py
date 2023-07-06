import re

import scrapy

from locations.items import Feature
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsBGSpider(scrapy.Spider):
    name = "mcdonalds_bg"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.bg"]
    start_urls = ("http://mcdonalds.bg/map/",)

    def parse(self, response):
        stores = response.css(".restaurant-info")
        for store in stores:
            ref = store.xpath(".//@data-post_id").extract_first()
            city = store.xpath(".//@data-city_title").extract_first()
            lat = store.xpath(".//@data-latitude").extract_first()
            lon = store.xpath(".//@data-longitude").extract_first()
            address = store.xpath(".//p[1]/text()").extract_first()

            phone = store.xpath(".//p[2]/text()").extract_first()
            if phone:
                match = re.search(r"Тел.(.*)", phone)
                if match:
                    phone = match.groups()[0].strip()

            properties = {
                "ref": ref,
                "phone": phone if phone else "",
                "lon": lon,
                "lat": lat,
                "city": city,
                "name": "McDonalds",
                "addr_full": address,
            }

            yield Feature(**properties)
