import scrapy

from locations.linked_data_parser import LinkedDataParser


class BestoneGBSpider(scrapy.spiders.SitemapSpider):
    name = "bestone_gb"
    item_attributes = {"brand": "Best-one", "brand_wikidata": "Q4896532"}
    sitemap_urls = ["https://stores.best-one.co.uk/sitemap.xml"]
    drop_attributes = {"name", "image"}

    def parse(self, response):
        for store_type in ["ConvenienceStore", "WholesaleStore"]:
            if item := LinkedDataParser.parse(response, store_type):
                yield item
                return
