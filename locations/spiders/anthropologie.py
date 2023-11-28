from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AnthropologieSpider(SitemapSpider, StructuredDataSpider):
    name = "anthropologie"
    item_attributes = {"brand": "Anthropologie", "brand_wikidata": "Q4773903"}
    allowed_domains = ["anthropologie.com"]
    sitemap_urls = ["https://www.anthropologie.com/store_sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_sd")]
    requires_proxy = True
