from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class MacysSpider(CrawlSpider, StructuredDataSpider):
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
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "referer": "https://www.macys.com/stores/ca/",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        },
    }
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        yield item
