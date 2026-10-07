from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PerkinsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "perkins_us"
    item_attributes = {"brand": "Perkins", "brand_wikidata": "Q7169056"}
    allowed_domains = ["www.perkinsrestaurants.com", "perkinsrestaurants.com"]
    sitemap_urls = ["https://perkinsrestaurants.com/sitemap.xml"]
    sitemap_rules = [(r"/location/.*$", "parse_sd")]
