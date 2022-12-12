from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PopeyesSpider(SitemapSpider, StructuredDataSpider):
    name = "popeyes"
    item_attributes = {"brand": "Popeyes", "brand_wikidata": "Q1330910"}
    sitemap_urls = ["https://locations.popeyes.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.popeyes.com/\w\w/.+/.+$", "parse_sd")]
