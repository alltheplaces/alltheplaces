from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.open_graph_spider import OpenGraphSpider


class FamilyShopperGBSpider(SitemapSpider, OpenGraphSpider):
    name = "family_shopper_gb"
    item_attributes = {
        "brand": "Family Shopper",
        "brand_wikidata": "Q122731426",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    sitemap_urls = ["https://www.familyshopperstores.co.uk/sitemap.xml"]
    sitemap_rules = [("/our-stores/", "parse")]

    def post_process_item(self, item, response, **kwargs):
        item["branch"] = (
            item.pop("name").removeprefix("Family Shopper").strip(" -").removeprefix("Family Shopper").strip(" -")
        )
        yield item
