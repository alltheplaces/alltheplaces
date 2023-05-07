from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AnntaylorSpider(SitemapSpider, StructuredDataSpider):
    name = "anntaylor"
    item_attributes = {"brand": "Ann Taylor", "brand_wikidata": "Q4766699"}
    allowed_domains = ["stores.anntaylor.com"]
    download_delay = 0
    sitemap_urls = ["https://stores.anntaylor.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://stores\.anntaylor\.com/\w\w/[-\w]+/[-\w]+\.html$", "parse_sd"),
        (r"https://stores\.anntaylor\.com/factory/\w\w/\w\w/[-\w]+/[-\w]+\.html$", "parse_sd"),
    ]
