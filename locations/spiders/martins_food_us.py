from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MartinsFoodUSSpider(SitemapSpider, StructuredDataSpider):
    name = "martins_food_us"
    item_attributes = {
        "brand": "Martin's",
        "brand_wikidata": "Q123028492",
        "operator": "Giant Food Stores",
        "operator_wikidata": "Q5558332",
    }
    allowed_domains = ["martinsfoods.com"]
    sitemap_urls = ["https://stores.martinsfoods.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/\d+-[^/]+$", "parse")]
    wanted_types = ["GroceryStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.xpath(
            '//div[@class="StoreDetails-storeNum"]/text()'
        ).get()
        item["branch"] = item.pop("name").removeprefix("MARTIN'S ")

        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
