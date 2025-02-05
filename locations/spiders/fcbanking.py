from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FcbankingSpider(SitemapSpider, StructuredDataSpider):
    name = "fcbanking"
    item_attributes = {"brand": "First Commonwealth Bank", "brand_wikidata": "Q5452773"}
    sitemap_urls = ["https://www.fcbanking.com/robots.txt"]
    sitemap_rules = [(r"/branch-locations/[-\w]+/[-\w]+/[-\w]+/[-\w]+", "parse_sd")]
    wanted_types = ["BankOrCreditUnion"]  # Capture only url specific linked data
