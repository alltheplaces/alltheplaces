import scrapy

from locations.open_graph_spider import OpenGraphSpider
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsBalticsSpider(scrapy.spiders.SitemapSpider, OpenGraphSpider):
    name = "mcdonalds_baltics"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    item_attributes = McdonaldsSpider.item_attributes
    sitemap_urls = [
        "https://mcdonalds.ee/location-sitemap.xml",
        "https://mcd.lt/location-sitemap.xml",
        "https://mcdonalds.lv/location-sitemap.xml",
    ]
    wanted_types = ["article"]
    requires_proxy = True

    def post_process_item(self, item, response, **kwargs):
        item["lat"] = response.xpath("//@data-lat").extract_first()
        item["lon"] = response.xpath("//@data-lng").extract_first()
        yield item
