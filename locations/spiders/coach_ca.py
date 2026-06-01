from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CoachCASpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "coach_ca"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}
    sitemap_urls = ["https://ca.coach.com/en/stores/sitemap.xml"]
    sitemap_rules = [(r"https://ca.coach.com/en/stores/[^/]+/[^/]+/[^/]+", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = (item.pop("name", "") or "").removeprefix("About ")
        item["name"] = response.xpath('//h4[@class="location-type mt-0 mb-10"]/text()').get()
        apply_category(Categories.SHOP_BAG, item)
        yield item
