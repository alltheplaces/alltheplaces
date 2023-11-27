from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


# AU, CA, GU, NZ, PR, US, VI
class SunglassHut1Spider(SitemapSpider, StructuredDataSpider):
    name = "sunglass_hut_1"
    item_attributes = {"brand": "Sunglass Hut", "brand_wikidata": "Q136311"}
    allowed_domains = ["stores.sunglasshut.com"]
    sitemap_urls = ["https://stores.sunglasshut.com/robots.txt"]
