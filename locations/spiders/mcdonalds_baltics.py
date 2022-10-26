# -*- coding: utf-8 -*-
import scrapy

from locations.open_graph_parser import OpenGraphParser
from locations.spiders.mcdonalds import McDonaldsSpider


def country_from_url(response):
    return response.url.split("/")[2].split(".")[-1].upper()


class McDonaldsBalticsSpider(scrapy.spiders.SitemapSpider):
    name = "mcdonalds_baltics"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    item_attributes = McDonaldsSpider.item_attributes
    sitemap_urls = [
        "https://mcdonalds.ee/location-sitemap.xml",
        "https://mcd.lt/location-sitemap.xml",
        "https://mcdonalds.lv/location-sitemap.xml",
    ]
    download_delay = 1.0

    def parse(self, response):
        item = OpenGraphParser.parse(response)
        item["country"] = country_from_url(response)
        item["lat"] = response.xpath("//@data-lat").extract_first()
        item["lon"] = response.xpath("//@data-lng").extract_first()
        yield item
