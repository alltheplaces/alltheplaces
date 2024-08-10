import scrapy

from locations.open_graph_spider import OpenGraphParser
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsBalticsSpider(scrapy.spiders.SitemapSpider, OpenGraphParser):
    name = "mcdonalds_baltics"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    item_attributes = McdonaldsSpider.item_attributes
    sitemap_urls = [
        "https://mcdonalds.ee/location-sitemap.xml",
        "https://mcd.lt/location-sitemap.xml",
        "https://mcdonalds.lv/location-sitemap.xml",
    ]

    def post_process_item(self, item, response, **kwargs):
        item["lat"] = response.xpath("//@data-lat").extract_first()
        item["lon"] = response.xpath("//@data-lng").extract_first()
        yield item
