from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RamenKairikiyaJPSpider(SitemapSpider, StructuredDataSpider):
    name = "ramen_kairikiya_jp"
    item_attributes = {
        "brand": "ラーメン魁力屋",
        "brand_wikidata": "Q11347773",
    }
    sitemap_urls = ["https://shop.kairikiya.co.jp/__sitemap__/ja.xml"]
    sitemap_rules = [(r"/stores/(\d+)$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Feature:
        item["branch"] = item.pop("name", None)
        apply_category(Categories.FAST_FOOD, item)
        yield item
