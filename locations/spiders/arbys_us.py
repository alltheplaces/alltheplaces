from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ArbysUSSpider(SitemapSpider, StructuredDataSpider):
    name = "arbys_us"
    item_attributes = {"brand": "Arby's", "brand_wikidata": "Q630866"}
    sitemap_urls = ["https://locations.arbys.com/sitemap.xml"]
    sitemap_rules = [(r"\.html$", "parse_sd")]
