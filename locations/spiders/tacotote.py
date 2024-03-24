import base64
import json
import re
import zlib

import scrapy

from locations.categories import Categories
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class TacototeSpider(WpGoMapsSpider):
    name = "tacotote"
    item_attributes = {
        "brand": "El Taco Tote",
        "brand_wikidata": "Q16992316",
        "extras": Categories.RESTAURANT.value,
    }
    allowed_domains = ["tacotote.com"]
    start_urls = ("https://tacotote.com/wp-sitemap-posts-page-1.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            if re.search(r"/locations-old/.", url):
                yield scrapy.Request(url, callback=self.parse_city)

    def parse_city(self, response):
        mapid = response.xpath("//@mapid").extract_first()
        param = {"filter": json.dumps({"map_id": mapid})}
        data = zlib.compress(json.dumps(param).encode())
        path = base64.b64encode(data).rstrip(b"=").decode()
        url = f"https://tacotote.com/wp-json/wpgmza/v1/features/base64{path}"
        yield scrapy.Request(url, callback=self.parse_stores)
