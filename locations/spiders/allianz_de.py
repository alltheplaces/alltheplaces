from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AllianzDESpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "allianz_de"
    item_attributes = {"brand": "Allianz", "brand_wikidata": "Q487292"}
    sitemap_urls = [
        "https://vertretung.allianz.de/sitemap.xml",
    ]
    sitemap_rules = [("", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["name"] = None
        item["phone"] = ld_data.get("telePhone", None)
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
