from scrapy import Request, Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS_WEEKDAY, OpeningHours

DAYS_TERMS = {
    "OpeningHours": DAYS_WEEKDAY,
    "SaturdayHours": "Sa",
    "SundayHours": "Su",
}


class CapitecBankZASpider(Spider):
    name = "capitec_bank_za"
    item_attributes = {"brand": "Capitec Bank", "brand_wikidata": "Q5035822"}
    allowed_domains = ["capitecbank.co.za"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True
    requires_proxy = "ZA"

    def start_requests(self):
        # Maximum returned is 100, even with larger "Take"
        # Even with 48km radius, not all locations are returned, and it is making ove 260 requests
        for lat, lon in country_iseadgg_centroids("ZA", 48):
            yield Request(
                url="https://www.capitecbank.co.za/api/Branch",
                body=f"Latitude={lat}&Longitude={lon}&Take=100",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )

    def parse(self, response):
        for location in response.json()["Branches"]:
            if location["IsClosed"]:
                continue
            item = DictParser.parse(location)
            if location["IsAtm"]:
                item["ref"] = location["Id"]
                apply_category(Categories.ATM, item)
                apply_yes_no(Extras.CASH_IN, item, location["CashAccepting"], False)
            else:
                item["ref"] = None
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
