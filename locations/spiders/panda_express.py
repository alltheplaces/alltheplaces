from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PandaExpressSpider(SitemapSpider, StructuredDataSpider):
    name = "panda_express"
    item_attributes = {"brand": "Panda Express", "brand_wikidata": "Q1358690"}
    sitemap_urls = ["https://www.pandaexpress.com/locations/sitemap.xml"]
    sitemap_rules = [(r"https://www.pandaexpress.com/locations/[^/]+/[^/]+/\d+$", "parse_sd")]
