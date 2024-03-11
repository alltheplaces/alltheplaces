from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KarweiNLSpider(SitemapSpider, StructuredDataSpider):
    name = "karwei_nl"
    item_attributes = {"brand": "Karwei", "brand_wikidata": "Q2097480"}
    sitemap_urls = ["https://sitemap.karwei.nl/stores.xml"]
    wanted_types = ["HardwareStore"]
