from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ElkjopNOSpider(SitemapSpider, StructuredDataSpider):
    name = "elkjop_no"
    item_attributes = {"name": "Elkjøp", "brand": "Elkjøp", "brand_wikidata": "Q1771628"}
    sitemap_urls = ["https://www.elkjop.no/robots.txt"]
    sitemap_rules = [("/store/elkjop-", "parse")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Elkjøp ")
        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
