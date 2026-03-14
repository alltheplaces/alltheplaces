import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours


class InduslandBankINSpider(scrapy.Spider):
    name = "indusland_bank_in"
    item_attributes = {"brand": "IndusInd Bank", "brand_wikidata": "Q2040323"}
    start_urls = ["https://www.indusind.bank.in/bin/branch/getAllLocation?id1=branchesNew&id2=atm"]

    def parse(self, response, **kwargs):
        for store in response.json():
            if "sNos" in store:
                item = DictParser.parse(store)
                if pincode := store.get("pincode"):
                    item["postcode"] = str(pincode).replace(".0", "")

                if store.get("identifiers") == "ATM":
                    apply_category(Categories.ATM, item)
                else:
                    apply_category(Categories.BANK, item)

                item["ref"] = "_".join([store.get("identifiers"), store.get("sNos")])
                item["opening_hours"] = self.parse_opening_hours(store)

                yield item

    def parse_opening_hours(self, store: dict) -> OpeningHours:
        # Add :00 if no minutes specified (e.g., "5 PM" -> "5:00 PM")
        def normalize(t):
            t = t.strip()
            if ":" not in t:
                t = t.replace(" ", ":00 ")
            return t

        oh = OpeningHours()
        try:
            if weekday_timing := store.get("weekdaysTiming"):
                if " to " in weekday_timing:
                    open_time, close_time = weekday_timing.split(" to ")
                    oh.add_days_range(DAYS_WEEKDAY, normalize(open_time), normalize(close_time), time_format="%I:%M %p")
            if store.get("satCloseOrOpenStatus") == "Open":
                if weekend_timing := store.get("weekendTiming"):
                    if " to " in weekend_timing:
                        open_time, close_time = weekend_timing.split(" to ")
                        oh.add_range("Sa", normalize(open_time), normalize(close_time), time_format="%I:%M %p")
        except Exception:
            pass
        return oh
