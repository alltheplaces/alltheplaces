from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KohlsSpider(SitemapSpider, StructuredDataSpider):
    name = "kohls"
    item_attributes = {"brand": "Kohl's", "brand_wikidata": "Q967265"}
    allowed_domains = ["www.kohls.com"]
    sitemap_urls = ["https://www.kohls.com/sitemap_store.xml"]
    sitemap_rules = [(r"/stores/[-\w]+/[-\w]+.shtml$", "parse_sd")]
    wanted_types = ["DepartmentStore"]
