from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AllstateInsuranceAgentsSpider(SitemapSpider, StructuredDataSpider):
    name = "allstate_insurance_agents"
    item_attributes = {"brand": "Allstate", "brand_wikidata": "Q2645636"}
    allowed_domains = ["agents.allstate.com"]
    sitemap_urls = ["https://agents.allstate.com/sitemap.xml"]
    wanted_types = ["InsuranceAgency"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace(": Allstate Insurance", "")
        yield item
