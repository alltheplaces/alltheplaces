from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.go_review_api import GoReviewApiSpider


class CapitecBankZASpider(GoReviewApiSpider):
    name = "capitec_bank_za"
    item_attributes = {"brand": "Capitec Bank", "brand_wikidata": "Q5035822"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 300}
    domain = "capitecpages.localpages.io"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["storeCode"]
        for location_type in ["Capitec Bank ATM", "Capitec Bank", "Capitec Business Centre"]:
            if location_type in item["name"]:
                item["branch"] = item["name"].split(location_type)[1].strip()
                item["name"] = location_type
                break
        location_attributes = [attribute["value"] for attribute in feature.get("attributes", [])]
        if "ATM" in location_attributes:
            apply_category(Categories.ATM, item)
            apply_yes_no(Extras.CASH_IN, item, "Cash Accepting ATM" in location_attributes, False)
        else:
            apply_category(Categories.BANK, item)
        # feature["operating_hours"] don't have whole week hours info, seems to provide a single day hours, hence ignored.
        yield item
