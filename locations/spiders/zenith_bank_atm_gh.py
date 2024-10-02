from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.zenith_bank_branch_gh import ZENITH_BANK_SHARED_ATTRIBUTES


class ZenithBankAtmGHSpider(Spider):
    name = "zenith_bank_atm_gh"
    start_urls = ["https://www.zenithbank.com.gh/tools-resources/atm-locator/"]
    item_attributes = ZENITH_BANK_SHARED_ATTRIBUTES
    no_refs = True

    def parse(self, response):
        for location in response.xpath('.//div[@class="vc_column-inner"]/.//li/a'):
            item = Feature()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["branch"] = location.xpath("text()").get()
            apply_category(Categories.ATM, item)
            yield item
