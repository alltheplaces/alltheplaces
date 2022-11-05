from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MoesSouthwestGrillSpider(SitemapSpider, StructuredDataSpider):
    name = "moes"
    item_attributes = {
        "brand": "Moe's Southwest Grill",
        "brand_wikidata": "Q6889938",
    }
    sitemap_urls = ["https://locations.moes.com/robots.txt"]
    sitemap_rules = [
        (r"locations\.moes\.com/.*/.*/.*$", "parse_sd"),
    ]
