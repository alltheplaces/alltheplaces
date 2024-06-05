import json

import scrapy

from locations.dict_parser import DictParser
from locations.linked_data_parser import LinkedDataParser

NANDOS_SHARED_ATTRIBUTES = {"brand": "Nando's", "brand_wikidata": "Q3472954"}


class NandosSpider(scrapy.spiders.SitemapSpider):
    name = "nandos"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    sitemap_urls = [
        "https://www.nandos.co.uk/sitemap.xml",  # This is GB and IE
        "https://www.nandos.com.au/sitemap.xml",
        "https://www.nandos.co.nz/sitemap.xml",
        "https://www.nandos.ca/sitemap.xml",
    ]
    # Different Nando's estates have slightly different approaches.
    sitemap_rules = [
        (".co.uk/restaurants/", "parse_ldjson"),
        (".com.au/restaurants/", "parse_json2"),
        (".co.nz/restaurants/", "parse_json2"),
        ("nandos.ca/find/", "parse_json1"),
    ]
    download_delay = 0.5
    skip_auto_cc_domain = True

    @staticmethod
    def country_from_url(response):
        country = response.url.split("/")[2].split(".")[-1].upper()
        if "COM" == country:
            return "US"
        elif "UK" == country:
            # Nando's does IE and GB with .uk!
            return None
        else:
            return country

    def parse_ldjson(self, response):
        if item := LinkedDataParser.parse(response, "Restaurant"):
            item["country"] = self.country_from_url(response)
            item["ref"] = response.url
            yield item

    def parse_json1(self, response):
        script = response.xpath('//script[@id="__NEXT_DATA__"]//text()').get()
        data = json.loads(script)
        site = DictParser.get_nested_key(data, "restaurants")[0]
        item = DictParser.parse(site)
        item["website"] = item["ref"] = response.url
        item["country"] = self.country_from_url(response)
        yield item

    def parse_json2(self, response):
        script = response.xpath('//script[@id="__NEXT_DATA__"]//text()').get()
        data = json.loads(script)
        if site := DictParser.get_nested_key(data, "restaurant"):
            item = DictParser.parse(site)
            item["website"] = item["ref"] = response.url
            item["country"] = self.country_from_url(response)
            yield item
