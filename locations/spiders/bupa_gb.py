from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature, set_closed
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT

BUPA = {"brand": "Bupa", "brand_wikidata": "Q931628"}


class BupaGBSpider(CrawlSpider, StructuredDataSpider, PlaywrightSpider):
    name = "bupa_gb"
    start_urls = ["https://www.bupa.co.uk/dental/dental-care/practices"]
    rules = [
        Rule(LinkExtractor(r"/practices/([-\w]+)$"), "parse_sd"),
        Rule(
            LinkExtractor(r"/browse-by-region/[-\w]+$"),
        ),
    ]
    requires_proxy = True
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if "Total Dental Care" in item["name"]:
            item["brand"] = "Total Dental Care"
        elif "Bupa" in item["name"]:
            item.update(BUPA)

        if item["name"].lower().endswith(" - closed"):
            set_closed(item)

        apply_category(Categories.DENTIST, item)

        yield item
