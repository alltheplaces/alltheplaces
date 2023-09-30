from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SunAutoServiceUSSpider(SitemapSpider, StructuredDataSpider):
    name = "sun_auto_service_us"
    item_attributes = {"brand": "Sun Auto Service", "brand_wikidata": "Q118383798"}
    sitemap_urls = ["https://www.sunautoservice.com/store-sitemap.xml"]
    wanted_types = ["AutoRepair"]
