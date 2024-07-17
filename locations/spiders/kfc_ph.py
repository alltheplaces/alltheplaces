from scrapy.spiders import SitemapSpider

from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class KfcPHSpider(SitemapSpider, StructuredDataSpider):
    name = "kfc_ph"
    item_attributes = KFC_SHARED_ATTRIBUTES
    allowed_domains = ["stores.kfc.com.ph"]
    sitemap_urls = ["https://stores.kfc.com.ph/robots.txt"]
    sitemap_rules = [(r"-fast-food-restaurant-.+-\d+\/Map$", "parse_sd")]
    wanted_types = ["Restaurant"]
    time_format = "%I:%M %p"
