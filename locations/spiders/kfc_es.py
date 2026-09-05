import re

import scrapy

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.user_agents import FIREFOX_LATEST

DAY_HOURS_FIELDS = dict(
    zip(
        DAYS,
        [
            "mondayHours",
            "tuesdayHours",
            "wednesdayHours",
            "thursdayHours",
            "fridayHours",
            "saturdayHours",
            "sundayHours",
        ],
    )
)


class KfcESSpider(scrapy.Spider):
    name = "kfc_es"
    item_attributes = KFC_SHARED_ATTRIBUTES
    start_urls = ["https://api.kfc.es/find-a-kfc/allstores"]
    # api.kfc.es hangs/times out on requests with a non-browser User-Agent
    # (e.g. the default ATP one) rather than returning an HTTP error.
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": FIREFOX_LATEST}
    requires_proxy = True

    def parse(self, response, **kwargs):
        for store in response.json():
            primary = store.get("primaryAttributes", {})
            business = store.get("googleBusinessData", {})

            # A small number of records use a comma as the decimal separator
            # for latitude/longitude instead of a period.
            for key in ("latitude", "longitude"):
                if isinstance(business.get(key), str):
                    business[key] = business[key].replace(",", ".")

            item = DictParser.parse({**primary, **business})
            item["branch"] = item.pop("name").removeprefix("KFC ")
            item["website"] = "https://www.kfc.es/encuentra-tu-kfc/" + primary["slug"]
            item["extras"]["ref:google:place_id"] = primary.get("googlePlaceId")

            item["opening_hours"] = self.parse_hours(business)

            dispositions = primary.get("dispositions", [])
            apply_yes_no(Extras.DELIVERY, item, "delivery" in dispositions, apply_positive_only=False)
            apply_yes_no(Extras.TAKEAWAY, item, "pickup" in dispositions, apply_positive_only=False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "drivethru" in dispositions, apply_positive_only=False)

            services = store.get("services", {})
            apply_yes_no(Extras.WIFI, item, services.get("freeWifi", False), apply_positive_only=False)
            apply_yes_no(Extras.OUTDOOR_SEATING, item, services.get("terraces", False), apply_positive_only=False)

            payment = store.get("payment", {})
            apply_yes_no(PaymentMethods.CASH, item, payment.get("cashPayment", False), apply_positive_only=False)
            apply_yes_no(PaymentMethods.CARDS, item, payment.get("cardPayment", False), apply_positive_only=False)

            apply_yes_no(
                Extras.WHEELCHAIR,
                item,
                store.get("accessibility", {}).get("wheelchairAccess", False),
                apply_positive_only=False,
            )

            apply_category(Categories.FAST_FOOD, item)

            yield item

    @staticmethod
    def parse_hours(business: dict) -> OpeningHours:
        # Most stores separate open/close times with "-", but a handful of
        # records use ";" instead, some use "." instead of ":" in a time,
        # some express a close time past midnight as e.g. "24:30", and a few
        # split shifts have two ranges in one field. Extracting all HH:MM-like
        # tokens, normalising hours >= 24, and pairing them up copes with all
        # these variants.
        oh = OpeningHours()
        for day, field in DAY_HOURS_FIELDS.items():
            hours = business.get(field) or ""
            times = [KfcESSpider.normalise_time(t) for t in re.findall(r"\d{1,2}[:.]\d{2}", hours)]
            for open_time, close_time in zip(times[0::2], times[1::2]):
                oh.add_range(day, open_time, close_time)
        return oh

    @staticmethod
    def normalise_time(token: str) -> str:
        hour, minute = token.replace(".", ":").split(":")
        return "{:02d}:{}".format(int(hour) % 24, minute)
