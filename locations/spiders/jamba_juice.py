from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class JambaJuiceSpider(SitemapSpider, StructuredDataSpider):
    name = "jamba_juice"
    item_attributes = {"brand": "Jamba Juice", "brand_wikidata": "Q3088784"}
    allowed_domains = ["jamba.com"]
    sitemap_urls = ["https://locations.jamba.com/sitemap.xml"]
    sitemap_rules = [(r"/[-\w]+/[-\w]+/[-\w]+", "parse_sd")]
    wanted_types = ["Restaurant"]
