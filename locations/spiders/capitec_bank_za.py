from typing import AsyncIterator

from scrapy.http import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.json_blob_spider import JSONBlobSpider

DAYS_TERMS = {
    "OpeningHours": DAYS_WEEKDAY,
    "SaturdayHours": "Sa",
    "SundayHours": "Su",
}


class CapitecBankZASpider(JSONBlobSpider):
    name = "capitec_bank_za"
    item_attributes = {"brand": "Capitec Bank", "brand_wikidata": "Q5035822"}
    locations_key = "Branches"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        # Maximum returned is 100, even with larger "Take"
        # Even with 48km radius, not all locations are returned, and it is making over 260 requests
        for lat, lon in country_iseadgg_centroids("ZA", 48):
            yield Request(
                url="https://www.capitecbank.co.za/api/Branch",
                body=f"Latitude={lat}&Longitude={lon}&Take=100",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )

    def post_process_item(self, item, response, location):
        if location["IsClosed"]:
            return
        if location["IsAtm"]:
            apply_category(Categories.ATM, item)
            apply_yes_no(Extras.CASH_IN, item, location["CashAccepting"], False)
        else:
            item["ref"] = location["Name"].lower().replace(" ", "-")
            apply_category(Categories.BANK, item)

        item["branch"] = item.pop("name")

        oh = OpeningHours()
        for day in DAYS_TERMS:
            if location[day] is not None:
                if location[day].startswith("Closed"):
                    oh.set_closed(DAYS_TERMS[day])
                else:
                    oh.add_ranges_from_string(location[day])
        item["opening_hours"] = oh.as_opening_hours()

        yield item
