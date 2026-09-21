from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GreatSouthernBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "great_southern_bank_us"
    item_attributes = {"brand": "Great Southern Bank"}
    sitemap_urls = ["https://locations.greatsouthernbank.com/sitemap.xml"]
    sitemap_rules = [(r"^https://locations\.greatsouthernbank\.com/great-southern-bank-[0-9a-f]+$", "parse_sd")]
    wanted_types = ["FinancialService", "AutomatedTeller"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "CLOSED" in item["name"].upper():
            return

        if city := item.get("city"):
            # Source data occasionally duplicates the city name, e.g.
            # "SpringfieldSpringfield".
            half = len(city) // 2
            if len(city) % 2 == 0 and city[:half] == city[half:]:
                item["city"] = city[:half]

        types = ld_data.get("@type", [])
        name = item["name"].upper()

        if "FinancialService" in types and "BankOrCreditUnion" not in types:
            # Loan production offices and commercial lending offices have no
            # teller or ATM services and aren't open for general banking.
            apply_category(Categories.OFFICE_FINANCIAL, item)
        elif "ATM" in name or "ITM" in name or "EXPRESS CENTER" in name:
            # Interactive Teller Machines and "Express Centers" are
            # unstaffed/video-teller-only kiosks, not full branches.
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, "AutomatedTeller" in types)

        yield item
