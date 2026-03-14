from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DartyFRSpider(SitemapSpider, StructuredDataSpider):
    name = "darty_fr"
    item_attributes = {"brand": "Darty", "brand_wikidata": "Q2439098"}
    sitemap_urls = ["https://magasin.darty.com/sitemap.xml"]
    sitemap_follow = ["locationsitemap"]
    sitemap_rules = [("magasin.darty.com", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.SHOP_ELECTRICAL, item)
        item["branch"] = item.pop("name").replace("DARTY ", "")
        item.pop("phone")
        yield item
