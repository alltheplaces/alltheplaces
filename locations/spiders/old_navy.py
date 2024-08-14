from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class OldNavySpider(SitemapSpider, StructuredDataSpider):
    name = "old_navy"
    item_attributes = {"brand": "Old Navy", "brand_wikidata": "Q2735242"}
    allowed_domains = ["oldnavy.gap.com"]
    sitemap_urls = ["https://oldnavy.gap.com/stores/sitemap.xml"]
    sitemap_rules = [(r"/stores/[-\w]+/[-\w]+/[-\w]+.html$", "parse_sd")]
    wanted_types = ["ClothingStore"]
