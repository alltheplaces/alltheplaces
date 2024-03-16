from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class PizzaHutFR(SitemapSpider, StructuredDataSpider):
    name = "pizza_hut_fr"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    PIZZA_HUT_DELIVERY = {"brand": "Pizza Hut Delivery", "brand_wikidata": "Q107293079"}
    sitemap_urls = ["https://www.pizzahut.fr/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.pizzahut\.fr\/huts\/[-\w]+\/([-.\w]+)\/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = merge_address_lines(item["street_address"])

        if item["website"].startswith("https://www.pizzahut.fr/huts/"):
            item.update(self.PIZZA_HUT_DELIVERY)
            apply_category(Categories.FAST_FOOD, item)
        else:
            apply_category(Categories.RESTAURANT, item)

        if not item["opening_hours"]:
            return

        yield item
