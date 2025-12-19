from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GiantFoodUSSpider(SitemapSpider, StructuredDataSpider):
    name = "giant_food_us"
    item_attributes = {"brand": "Giant", "brand_wikidata": "Q5558336"}
    allowed_domains = ["giantfood.com"]
    sitemap_urls = ["https://stores.giantfood.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/\d+-[^/]+$", "parse")]
    wanted_types = ["GroceryStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.xpath('//div[@class="StoreDetails-storeNum"]/text()').get()
        item["branch"] = item.pop("name").removeprefix("Giant Food ")

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
