from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy import Request

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category


class MauboussinSpider(CrawlSpider, StructuredDataSpider):
    name = "mauboussin"
    item_attributes = {
        "brand": "Mauboussin",
        "brand_wikidata": "Q3300085",
    }
    allowed_domains = ["boutiques.mauboussin.fr"]
    start_urls = [ "https://boutiques.mauboussin.fr/boutiquesmauboussin/en/load-stores/location_country/whosonfirst:country:85633147"]
    drop_attributes = {"image", "twitter", "facebook"}

    #restrict_xpaths used to keep only mauboussin stores, not other stores selling mauboussin products
    rules = [Rule(
        LinkExtractor(
        allow=r"https://boutiques.mauboussin.fr/boutiquesmauboussin/en/store/france/",
        restrict_xpaths='//div[contains(@class, "accordion-store") and normalize-space(@data-grouping)="Store"]'
    ), callback="parse_sd")]

    def iter_linked_data(self, response):
        """ Extract only the first POI on the page and ignore the others, which may be shops that only distribute mauboussin items. """
        for ld_item in super().iter_linked_data(response):
            yield ld_item
            break

    def post_process_item(self, item, response, ld_data):
        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
