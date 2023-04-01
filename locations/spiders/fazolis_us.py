from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FazolisUSSpider(SitemapSpider, StructuredDataSpider):
    name = "fazolis_us"
    item_attributes = {"brand": "Fazoli's", "brand_wikidata": "Q1399195"}
    sitemap_urls = ["https://locations.fazolis.com/robots.txt"]
    sitemap_rules = [(r"https://locations\.fazolis\.com/\w\w/[-\w]+/[-\w]+\.html$", "parse_sd")]
