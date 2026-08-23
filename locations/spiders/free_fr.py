from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FreeFRSpider(SitemapSpider, StructuredDataSpider):
    name = "free_fr"
    item_attributes = {"brand": "Free", "brand_wikidata": "Q2467627"}
    sitemap_urls = ["https://www.free.fr/sitemap.xml"]
    sitemap_rules = [(r"/boutiques/boutique-\d+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Boutique Free ")
        item["name"] = self.item_attributes["brand"]
        apply_category(Categories.SHOP_TELECOMMUNICATION, item)
        yield item
