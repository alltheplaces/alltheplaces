from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BuckleSpider(SitemapSpider, StructuredDataSpider):
    name = "buckle"
    item_attributes = {
        "brand": "Buckle",
        "brand_wikidata": "Q4983306",
    }

    allowed_domains = ["local.buckle.com"]
    sitemap_urls = [
        "https://local.buckle.com/robots.txt",
    ]
    sitemap_rules = [(r"https://local\.buckle\.com/.*\d/", "parse")]
    json_parser = "json5"
