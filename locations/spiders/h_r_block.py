from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class HRBlockSpider(SitemapSpider, StructuredDataSpider):
    name = "h_r_block"
    item_attributes = {"brand": "H&R Block", "brand_wikidata": "Q5627799"}
    sitemap_urls = ["https://www.hrblock.com/sitemap.xml"]
    sitemap_rules = [(r"https://www\.hrblock\.com/local-tax-offices/[^/]+/[^/]+/[^/]+/\d+/$", "parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "DOWNLOADER_MIDDLEWARES": {"scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware": None},
        "USER_AGENT": BROWSER_DEFAULT,
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        },
    }
    sitemap_follow = ["opp"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.xpath("//@data-office-id").get()
        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()
        yield item
