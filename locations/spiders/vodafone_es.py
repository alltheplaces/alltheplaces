from scrapy.spiders import SitemapSpider

from locations.spiders.vodafone_de import VODAFONE_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class VodafoneESSpider(SitemapSpider, StructuredDataSpider):
    name = "vodafone_es"
    item_attributes = VODAFONE_SHARED_ATTRIBUTES
    allowed_domains = ["vodafone.es"]
    sitemap_urls = ["https://tiendas.vodafone.es/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/tiendas.vodafone.es\/tiendas\/.+\/.+\/.+", "parse_sd")]
    wanted_types = ["MobilePhoneStore"]
