from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class TaxAssistGBSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "tax_assist_gb"
    item_attributes = {"brand": "TaxAssist Accountants", "brand_wikidata": "Q122459380"}
    sitemap_urls = ["https://www.taxassist.co.uk/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS
    wanted_types = [
        ["AccountingService", "FinancialService", "LocalBusiness"],
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        yield item
