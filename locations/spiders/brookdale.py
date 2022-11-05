import json
import re
import urllib.parse
from pathlib import Path

import scrapy

from locations.linked_data_parser import LinkedDataParser


class BrookdaleSpider(scrapy.spiders.SitemapSpider):
    name = "brookdale"
    item_attributes = {"brand": "Brookdale", "brand_wikidata": "Q4974387"}
    allowed_domains = ["www.brookdale.com"]
    sitemap_urls = [
        "https://www.brookdale.com/robots.txt",
    ]
    sitemap_rules = [
        (r"/communities/[^/]+$", "parse"),
    ]

    def parse(self, response):
        if response.request.meta.get("redirect_reasons") == [301]:
            # Returning 301 when should be 404
            return

        script = response.xpath('//script[@type="application/ld+json"]/text()').get()
        script = script.replace('"amenityFeature": \n}', '"amenityFeature": [] \n}')
        script = script.replace("\r\n", "")
        script = re.sub(r'"description":.*', "", script)
        item = LinkedDataParser.parse_ld(json.loads(script))
        path = urllib.parse.urlsplit(response.url).path
        item["ref"] = Path(path).stem.removeprefix("brookdale-")
        yield item
