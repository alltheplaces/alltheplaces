import json

import scrapy

from locations.dict_parser import DictParser

NANDOS_SHARED_ATTRIBUTES = {"brand": "Nando's", "brand_wikidata": "Q3472954"}


class NandosSpider(scrapy.spiders.SitemapSpider):
    name = "nandos"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    sitemap_urls = [
        "https://www.nandos.com.au/sitemap.xml",
        "https://www.nandos.co.nz/sitemap.xml",
        "https://www.nandos.ca/sitemap.xml",
    ]
    # Different Nando's estates have slightly different approaches.
    sitemap_rules = [
        (".com.au/restaurants/", "parse_json2"),
        (".co.nz/restaurants/", "parse_json2"),
        ("nandos.ca/find/", "parse_json1"),
    ]

    def parse_json1(self, response):
        script = response.xpath('//script[@id="__NEXT_DATA__"]//text()').get()
        data = json.loads(script)
        site = DictParser.get_nested_key(data, "restaurants")[0]
        item = DictParser.parse(site)
        item["website"] = item["ref"] = response.url
        yield item

    def parse_json2(self, response):
        script = response.xpath('//script[@id="__NEXT_DATA__"]//text()').get()
        data = json.loads(script)
        if site := DictParser.get_nested_key(data, "restaurant"):
            item = DictParser.parse(site)
            item["website"] = item["ref"] = response.url
            yield item
