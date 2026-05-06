from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CoachSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "coach"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}

    sitemap_urls = [
        "https://uk.coach.com/stores/sitemap.xml",
        "https://de.coach.com/stores/sitemap.xml",
        "https://fr.coach.com/stores/sitemap.xml",
        "https://it.coach.com/stores/sitemap.xml",
        "https://es.coach.com/stores/sitemap.xml",
    ]

    sitemap_rules = [(r"/stores/[^/]+/[^/]+/[^/]+(?:\.html)?/?$", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs):
        raw_name = item.pop("name", "")
        prefixes_to_remove = ["About ", "Ã€ propos ", "À propos ", "Acerca de ", "Di ", "Um "]

        for prefix in prefixes_to_remove:
            if raw_name.startswith(prefix):
                raw_name = raw_name.removeprefix(prefix).strip()
                break

        item["branch"] = raw_name
        apply_category(Categories.SHOP_BAG, item)

        yield item
