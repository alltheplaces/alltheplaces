from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class OutbackSteakhouseSpider(SitemapSpider, StructuredDataSpider):
    name = "outback_steakhouse"
    item_attributes = {"brand": "Outback Steakhouse", "brand_wikidata": "Q1064893"}
    sitemap_urls = ["https://locations.outback.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.outback.com/.+/.+/.+", "parse_sd")]
