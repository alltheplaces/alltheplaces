from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class HRBlockSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "h_r_block"
    item_attributes = {"brand": "H&R Block", "brand_wikidata": "Q5627799"}
    sitemap_urls = ["https://www.hrblock.com/sitemap.xml"]
    sitemap_rules = [(r"/tax-office-near-me/[^/]+/[^/]+/\d+/?$", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000,
        "METAREFRESH_ENABLED": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "ROBOTSTXT_OBEY": False,
    }
    sitemap_follow = ["opp"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.xpath("//@data-office-id").get()
        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()
        yield item
