from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature, set_closed
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class PizzaHutFRSpider(SitemapSpider, StructuredDataSpider):
    name = "pizza_hut_fr"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    sitemap_urls = ["https://www.pizzahut.fr/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.pizzahut\.fr\/huts\/[-\w]+\/([-.\w]+)\/$", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if not item["opening_hours"]:
            set_closed(item)

        item["branch"] = item.pop("name").removeprefix("Pizza Hut ")

        apply_category(Categories.RESTAURANT, item)

        yield item
