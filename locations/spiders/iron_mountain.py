import scrapy

from locations.categories import Categories, apply_category
from locations.open_graph_parser import OpenGraphParser


class IronMountainSpider(scrapy.spiders.SitemapSpider):
    name = "iron_mountain"
    item_attributes = {"brand": "Iron Mountain Incorporated", "brand_wikidata": "Q1673079"}
    sitemap_urls = ["https://locations.ironmountain.com/robots.txt"]

    def parse(self, response):
        item = OpenGraphParser.parse(response)
        apply_category(Categories.OFFICE_COMPANY, item)
        if item["lat"]:
            yield item
