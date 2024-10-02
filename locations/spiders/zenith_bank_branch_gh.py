from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature

ZENITH_BANK_SHARED_ATTRIBUTES = {"brand": "Zenith Bank", "brand_wikidata": "Q5978240"}


class ZenithBankBranchGH(Spider):
    name = "zenith_bank_branch_gh"
    start_urls = ["https://www.zenithbank.com.gh/about-us/branches/"]
    item_attributes = ZENITH_BANK_SHARED_ATTRIBUTES
    no_refs = True

    def parse(self, response):
        for location in response.xpath('.//div[@class="bordered-container"]'):
            item = Feature()
            item["branch"] = location.xpath(".//h2/span/text()").get()
            extract_google_position(item, location)
            apply_category(Categories.BANK, item)
            yield item
            # TODO phone numbers, address and opening hours, but HTML is not easy to parse
