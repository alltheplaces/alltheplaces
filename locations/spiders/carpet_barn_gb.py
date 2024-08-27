from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CarpetBarnGBSpider(SitemapSpider, StructuredDataSpider):
    name = "carpet_barn_gb"
    item_attributes = {"brand": "Carpet Barn"}
    sitemap_urls = ["https://www.carpetsandbeds.com/robots.txt"]
    sitemap_rules = [(r"https://www.carpetsandbeds.com/carpet-barn-store-", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        item["image"] = None
        item["name"], item["branch"] = item["name"].rsplit(" ", 1)

        apply_category(Categories.SHOP_CARPET, item)

        yield item
