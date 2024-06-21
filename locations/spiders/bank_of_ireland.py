import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class BankOfIrelandSpider(CrawlSpider):
    name = "bank_of_ireland"
    item_attributes = {"brand": "Bank of Ireland", "brand_wikidata": "Q806689"}
    start_urls = ["https://www.bankofireland.com/branch-listing/"]
    rules = [Rule(LinkExtractor(allow=r"/branch-locator/[0-9a-z]+"), callback="parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = "Bank of Ireland"
        item["ref"] = item["website"] = response.url
        item["addr_full"], item["phone"] = re.search(
            r"Address:(.*)BOI Direct:\s*(.*)?\.", response.xpath(r'//*[@id = "meta-description"]/@content').get()
        ).groups()
        apply_category(Categories.BANK, item)

        yield item
