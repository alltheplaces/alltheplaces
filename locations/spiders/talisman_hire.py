from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TalismanHireSpider(SitemapSpider, StructuredDataSpider):
    name = "talisman_hire"
    item_attributes = {"brand": "Talisman Hire", "brand_wikidata": "Q120885726"}
    allowed_domains = ["www.talisman.co.za"]
    sitemap_urls = ["https://www.talisman.co.za/googlesitemap"]
    sitemap_rules = [(r"talisman\.co\.za/[-\w]+/[-\w]+/talisman-hire-[-\w]+$", "parse_sd")]
