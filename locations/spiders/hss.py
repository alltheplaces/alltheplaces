from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HssSpider(SitemapSpider, StructuredDataSpider):
    name = "hss"
    item_attributes = {
        "brand": "HSS Hire",
        "brand_wikidata": "Q5636000",
    }
    sitemap_urls = ["https://www.hss.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.hss.com/hire/find-a-branch/[\w-]+/[\w-]+", "parse"),
    ]
