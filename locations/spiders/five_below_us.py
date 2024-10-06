from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FiveBelowUSSpider(SitemapSpider, StructuredDataSpider):
    name = "five_below_us"
    item_attributes = {"brand": "Five Below", "brand_wikidata": "Q5455836"}
    drop_attributes = {"image", "name"}
    allowed_domains = ["locations.fivebelow.com"]
    sitemap_urls = ["https://locations.fivebelow.com/sitemap.xml"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["Store"]
