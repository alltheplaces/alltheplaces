# -*- coding: utf-8 -*-
import json
import re

from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class WyndhamSpider(SitemapSpider):
    name = "wyndham"
    download_delay = 1
    allowed_domains = ["www.wyndhamhotels.com"]
    sitemap_urls = ["https://www.wyndhamhotels.com/sitemap.xml"]
    sitemap_follow = [
        r"https:\/\/www\.wyndhamhotels\.com\/sitemap_en-us_([\w]{2})_properties_\d\.xml"
    ]
    sitemap_rules = [
        (
            r"https:\/\/www\.wyndhamhotels\.com\/([-\w]+)\/([-\w]+)\/([-\w]+)\/overview",
            "parse_property",
        )
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_property(self, response):
        raw_json = re.search(
            r'<script type="application\/ld\+json"\>(.+?)\<',
            response.text,
            flags=re.DOTALL,
        )
        if not raw_json:
            return None
        data = json.loads(raw_json.group(1).replace("\t", " "))
        properties = {
            "ref": response.url.replace("https://www.wyndhamhotels.com/", "").replace(
                "/overview", ""
            ),
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "name": data["name"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"].get("addressRegion"),
            "postcode": data["address"].get("postalCode"),
            "country": data["address"].get("addressCountry"),
            "phone": data["telephone"],
            "website": response.url,
            "brand": re.match(self.sitemap_rules[0][0], response.url).group(1),
        }
        yield GeojsonPointItem(**properties)
