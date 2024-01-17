from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KfcPHSpider(SitemapSpider, StructuredDataSpider):
    name = "kfc_ph"
    item_attributes = {"brand": "KFC", "brand_wikidata": "Q524757"}
    allowed_domains = ["stores.kfc.com.ph"]
    sitemap_urls = ["https://stores.kfc.com.ph/sitemap.xml"]
    sitemap_rules = [(r"-fast-food-restaurant-.+-\d+\/Map$", "parse_sd")]
    wanted_types = ["Restaurant"]
    time_format = "%I:%M %p"
