import re

import scrapy

from locations.linked_data_parser import LinkedDataParser


class PublicStorageSpider(scrapy.Spider):
    name = "public_storage"
    item_attributes = {"brand": "Public Storage"}
    allowed_domains = ["www.publicstorage.com"]
    start_urls = [
        "https://www.publicstorage.com/site-map-states",
    ]

    def parse(self, response):
        yield from response.follow_all(css=".ps-sitemap-states__states a")
        for link in response.follow_all(css='a[href^="/self-storage-"]'):
            if re.search(r"/self-storage-[a-z-]+(/\d+)$", link.url):
                yield link
        yield LinkedDataParser.parse(response, "SelfStorage")
