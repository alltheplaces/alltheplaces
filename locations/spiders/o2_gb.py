from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class O2GBSpider(SitemapSpider, StructuredDataSpider):
    name = "o2_gb"
    item_attributes = {"brand": "O2", "brand_wikidata": "Q1759255"}
    sitemap_urls = ["https://stores.o2.co.uk/robots.txt"]
    sitemap_rules = [("/o2-store-", "parse_sd")]
    wanted_types = ["MobilePhoneStore"]
