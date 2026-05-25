from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import CHROME_LATEST


class MacysSpider(CrawlSpider, StructuredDataSpider, PlaywrightSpider):
    name = "macys"
    item_attributes = {"brand": "Macy's", "brand_wikidata": "Q629269"}
    allowed_domains = ["www.macys.com"]
    start_urls = ["https://www.macys.com/stores/browse/"]
    rules = [
        Rule(LinkExtractor(r"/stores/\w\w/$")),
        Rule(LinkExtractor(r"/stores/\w\w/[^/]+/$")),
        Rule(LinkExtractor(r"/stores/\w\w/[^/]+/[^/]+\_(\d+).html$"), "parse"),
    ]
    wanted_types = ["Store"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "referer": "https://www.macys.com/stores/ca/",
            "user-agent": CHROME_LATEST,
        },
    }

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        yield item
