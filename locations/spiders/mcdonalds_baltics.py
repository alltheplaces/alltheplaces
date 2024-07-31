import scrapy

from locations.open_graph_parser import OpenGraphParser
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsBalticsSpider(scrapy.spiders.SitemapSpider):
    name = "mcdonalds_baltics"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    item_attributes = McdonaldsSpider.item_attributes
    sitemap_urls = [
        "https://mcdonalds.ee/location-sitemap.xml",
        "https://mcd.lt/location-sitemap.xml",
        "https://mcdonalds.lv/location-sitemap.xml",
    ]

    def parse(self, response):
        item = OpenGraphParser.parse(response)
        item["lat"] = response.xpath("//@data-lat").extract_first()
        item["lon"] = response.xpath("//@data-lng").extract_first()
        yield item
