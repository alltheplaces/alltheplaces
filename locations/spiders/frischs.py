from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FrischsSpider(SitemapSpider, StructuredDataSpider):
    name = "frischs"
    item_attributes = {
        "brand": "Frisch's Big Boy",
        "brand_wikidata": "Q5504660",
    }
    allowed_domains = ["locations.frischs.com"]
    sitemap_urls = [
        "https://locations.frischs.com/robots.txt",
    ]
    sitemap_rules = [
        (r"/\d+/$", "parse_sd"),
    ]
    json_parser = "chompjs"
