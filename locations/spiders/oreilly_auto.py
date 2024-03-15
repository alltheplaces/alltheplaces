from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class OreillyAutoSpider(SitemapSpider, StructuredDataSpider):
    name = "oreilly"
    item_attributes = {"brand": "O'Reilly Auto Parts", "brand_wikidata": "Q7071951"}
    allowed_domains = ["locations.oreillyauto.com"]
    sitemap_urls = ["https://locations.oreillyauto.com/sitemap.xml"]
    sitemap_rules = [(r"[0-9]+.html$", "parse_sd")]
    wanted_types = ["AutoPartsStore"]
    requires_proxy = True
