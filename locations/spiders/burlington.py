from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BurlingtonUSSpider(SitemapSpider, StructuredDataSpider):
    name = "burlington_us"
    sitemap_urls = ["https://stores.burlington.com/robots.txt"]
    sitemap_rules = [(r"^https://stores\.burlington\.com/.*/.*/.*/$", "parse")]
    item_attributes = {
        "brand": "Burlington",
        "brand_wikidata": "Q4999220",
    }
