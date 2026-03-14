import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AlliedIrishBanksIESpider(SitemapSpider, StructuredDataSpider):
    name = "allied_irish_banks_ie"
    item_attributes = {"brand": "AIB", "brand_wikidata": "Q1642179"}
    sitemap_urls = ["https://branches.aib.ie/robots.txt"]
    sitemap_rules = [(r"https://branches.aib.ie/.+/.+/.+", "parse_sd")]
    wanted_types = ["BankOrCreditUnion"]
    drop_attributes = {"image"}

    def pre_process_data(self, ld_data: dict, **kwargs):
        new_rules = []
        for rule in ld_data["openingHours"]:
            if m := re.match(r"(\w\w) (\d\d:\d\d-\d\d:\d\d) (\d\d:\d\d-\d\d:\d\d)", rule):
                rule = "{} {},{}".format(*m.groups())
            new_rules.append(rule)
        ld_data["openingHours"] = new_rules

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = (
            item.pop("name")
            .removeprefix("AIB Glanmire")
            .removeprefix("AIB Bank Castleblayney")
            .removeprefix("AIB Bank")
            .strip(" -")
        )

        # Extract ATM information from makesOffer
        services = [service.get("name") for service in ld_data.get("makesOffer", []) if service.get("name")]
        has_atm = any("ATM" in service for service in services)
        apply_yes_no(Extras.ATM, item, has_atm)

        if has_atm:
            # Check if ATM has deposit capability (ATM & Lodge)
            has_deposit = any("ATM" in service and "Lodge" in service for service in services)
            apply_yes_no(Extras.CASH_IN, item, has_deposit)

        apply_category(Categories.BANK, item)

        yield item
