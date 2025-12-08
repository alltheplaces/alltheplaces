import scrapy

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsCZSpider(scrapy.Spider):
    name = "mcdonalds_cz"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.cz"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = (
        "https://restaurace.mcdonalds.cz/api?token=7983978c4175e5a88b9a58e5b5c6d105217fbc625b6c20e9a8eef3b8acc6204f",
    )

    def parse_hours(self, item, poi):
        if worktime := poi.get("worktime"):
            oh = OpeningHours()
            try:
                for day, times in zip(DAYS, worktime):
                    open, close = times.split(" - ")
                    oh.add_range(day, open.strip(), close.strip())
                item["opening_hours"] = oh
            except:
                self.logger.warning(f"Couldn't parse opening hours: {worktime}")

    def parse(self, response):
        pois = response.json().get("restaurants")
        for poi in pois:
            if poi["slug"] == "test-lsm":
                continue

            poi["street_address"] = poi.pop("address")
            item = DictParser.parse(poi)
            item["branch"] = item.pop("name")
            item["website"] = response.urljoin(poi["slug"])
            item["postcode"] = str(item["postcode"])
            self.parse_hours(item, poi)

            apply_yes_no(Extras.WIFI, item, "wifi" in poi["categories"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, "mcdrive" in poi["categories"])
            apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "amex" in poi["categories"])
            apply_yes_no(PaymentMethods.MASTER_CARD, item, "mastercard" in poi["categories"])
            apply_yes_no(PaymentMethods.VISA, item, "visa" in poi["categories"])
            # TODO: other payment methods include:
            #  chequedejeuner club cup darkove doxx edenred eur gastropass isic master nasestravenkaa ticket usd visael

            yield item
