from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DefactoTRSpider(SitemapSpider, StructuredDataSpider):
    name = "defacto_tr"
    item_attributes = {"brand": "DeFacto", "brand_wikidata": "Q6059861"}
    sitemap_urls = ["https://www.defacto.com.tr/sharedxml/tr-stores.xml"]
    sitemap_rules = [(r"/magazalar/.*[0-9]$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.SHOP_CLOTHES, item)
        item["branch"] = item.pop("name")
        yield item
