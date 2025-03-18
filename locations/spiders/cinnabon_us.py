from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CinnabonUSSpider(SitemapSpider, StructuredDataSpider):
    name = "cinnabon_us"
    item_attributes = {"brand": "Cinnabon", "brand_wikidata": "Q1092539"}
    sitemap_urls = ["https://locations.cinnabon.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.cinnabon.com/.+?/.+?/.+", "parse_sd")]
