import re
from typing import Any

from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class BankOfIrelandSpider(Spider):
    name = "bank_of_ireland"
    item_attributes = {"brand": "Bank of Ireland", "brand_wikidata": "Q806689"}
    start_urls = [
        "https://personalbanking.bankofireland.com/ways-to-bank/branch-banking/external-lodgement-atm-locations/",
        "https://www.bankofireland.com/branch-listing/",
    ]
    link_extractor = LinkExtractor(allow=r"/branch-locator/[-\w]+")
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        """
        ATM availability information cannot be extracted using Scrapy from the branch page,
        as the branch services are loaded dynamically.
        To work around this, we use a separate list of branches with ATMs to identify ATM locations.
        """
        for link in self.link_extractor.extract_links(response):
            is_atm = False
            if "atm-locations" in response.url:
                is_atm = True
            yield Request(link.url, callback=self.parse_location, cb_kwargs=dict(is_atm=is_atm), dont_filter=True)

    def parse_location(self, response: Response, is_atm: bool) -> Any:

        item = Feature()
        item["name"] = "Bank of Ireland"
        slug = response.url.strip("/").split("/")[-1]
        item["ref"] = slug
        item["branch"] = slug.title().replace("-", " ")
        item["website"] = response.url
        item["addr_full"], item["phone"] = re.search(
            r"Address:(.*)BOI Direct:\s*(.*)?\.", response.xpath(r'//*[@id = "meta-description"]/@content').get()
        ).groups()

        if is_atm:  # All are lodgement ATMs i.e. deposit-capable.
            item["ref"] += "-atm"
            item.pop("phone")
            apply_category(Categories.ATM, item)
            apply_yes_no(Extras.CASH_IN, item, True)
            apply_yes_no(Extras.CASH_OUT, item, True)
        else:
            apply_category(Categories.BANK, item)

        yield item
