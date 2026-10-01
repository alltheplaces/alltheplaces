from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HotshotsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "hotshots_us"
    item_attributes = {"brand": "Hotshots Sports Bar and Grill", "brand_wikidata": "Q130344931"}
    sitemap_urls = ["https://hotshotsnet.com/location-sitemap.xml"]
    sitemap_rules = [(r"/locations/([^/]+)/$", "parse")]
    wanted_types = ["Restaurant"]
    drop_attributes = {"name"}
