from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature, set_closed
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class EtosNLSpider(SitemapSpider, StructuredDataSpider):
    name = "etos_nl"
    item_attributes = {"brand": "Etos", "brand_wikidata": "Q2609459"}
    sitemap_urls = [
        "https://www.etos.nl/sitemap-store_custom_sitemap.xml",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if all(rule.get("opens") == "null" for rule in ld_data.get("openingHoursSpecification", [])):
            set_closed(item)
        item["branch"] = item.pop("name").title().removeprefix("Etos ")
        apply_category(Categories.SHOP_CHEMIST, item)
        yield item
