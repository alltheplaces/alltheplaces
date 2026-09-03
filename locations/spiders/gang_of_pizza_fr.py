from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class GangOfPizzaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "gang_of_pizza_fr"
    item_attributes = {"brand": "Gang of Pizza", "brand_wikidata": "Q89123626"}
    sitemap_urls = ["https://distributeurs.gangofpizza.com/sitemap.xml"]
    sitemap_rules = [("/gang-of-pizza-", "parse_sd")]
    wanted_types = ["FoodEstablishment"]
    drop_attributes = {"facebook", "image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = (item.pop("name", "") or "").removeprefix("Gang Of Pizza ")
        apply_category(Categories.VENDING_MACHINE, item)
        yield item
