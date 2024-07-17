from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CasinoFRSpider(CrawlSpider, StructuredDataSpider):
    name = "casino_fr"
    item_attributes = {"brand": "Casino Supermarchés", "brand_wikidata": "Q89029184"}
    allowed_domains = ["magasins.supercasino.fr"]
    start_urls = ["https://magasins.supercasino.fr/fr"]
    rules = [Rule(LinkExtractor("/supermarche/"), "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
