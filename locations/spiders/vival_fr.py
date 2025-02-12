from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class VivalFRSpider(SitemapSpider, StructuredDataSpider):
    name = "vival_fr"
    item_attributes = {"brand": "Vival", "brand_wikidata": "Q7937525"}
    sitemap_urls = ["https://magasins.vival.fr/robots.txt"]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}
