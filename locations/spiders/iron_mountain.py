import scrapy

from locations.categories import Categories, apply_category
from locations.open_graph_spider import OpenGraphSpider


class IronMountainSpider(scrapy.spiders.SitemapSpider, OpenGraphSpider):
    name = "iron_mountain"
    item_attributes = {"brand": "Iron Mountain Incorporated", "brand_wikidata": "Q1673079"}
    sitemap_urls = ["https://locations.ironmountain.com/robots.txt"]

    def post_process_item(self, item, response, **kwargs):
        apply_category(Categories.OFFICE_COMPANY, item)
        if item["lat"]:
            yield item
