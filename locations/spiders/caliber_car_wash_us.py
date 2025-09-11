from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CaliberCarWashUSSpider(SitemapSpider, StructuredDataSpider):
    name = "caliber_car_wash_us"
    item_attributes = {"brand": "Caliber Car Wash", "brand_wikidata": "Q131937909"}
    sitemap_urls = ["https://calibercarwash.com/3owllocations-sitemap.xml"]
    sitemap_rules = [(r"/location/[^/]+/$", "parse")]
    custom_settings = {"DOWNLOAD_DELAY": 10}
    drop_attributes = ["name"]
    search_for_facebook = False
    wanted_types = ["AutoWash"]
