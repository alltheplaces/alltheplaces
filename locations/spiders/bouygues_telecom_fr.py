from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BouyguesTelecomFRSpider(SitemapSpider, StructuredDataSpider):
    name = "bouygues_telecom_fr"
    item_attributes = {"brand": "Bouygues Telecom", "brand_wikidata": "Q581438"}
    sitemap_urls = ["https://boutiques.bouyguestelecom.fr/sitemap.xml"]
    sitemap_rules = [("/shop/", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("BOUYGUES TELECOM ")
        item["name"] = self.item_attributes["brand"]
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
