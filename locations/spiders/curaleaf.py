from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider


class CuraleafSpider(SitemapSpider, StructuredDataSpider):
    name = "curaleaf"
    item_attributes = {"brand": "Curaleaf", "brand_wikidata": "Q85754829"}
    allowed_domains = ["curaleaf.com"]
    sitemap_urls = ["https://curaleaf.com/sitemap-0.xml"]
    sitemap_rules = [("/shop/", "parse_sd")]
    wanted_types = ["Store"]
