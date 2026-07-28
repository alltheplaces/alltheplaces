from scrapy.spiders import SitemapSpider

from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class KarweiNLSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "karwei_nl"
    item_attributes = {"brand": "Karwei", "brand_wikidata": "Q2097480"}
    sitemap_urls = ["https://sitemap.karwei.nl/stores.xml"]
    wanted_types = ["HardwareStore"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS 
    requires_proxy = True
