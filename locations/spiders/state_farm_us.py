from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class StateFarmUSSpider(SitemapSpider, StructuredDataSpider):
    name = "state_farm_us"
    item_attributes = {"brand": "State Farm", "brand_wikidata": "Q2007336", "country": "US"}
    sitemap_urls = ["https://www.statefarm.com/sitemap-agents.xml"]
    sitemap_rules = [(r"/agent/us/\w\w/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["InsuranceAgency"]
    requires_proxy = True
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS": 1,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": BROWSER_DEFAULT,
        },
    }

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url.rsplit("/", 1)[1]
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
