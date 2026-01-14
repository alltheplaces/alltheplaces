import scrapy

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
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

    def parse_hours(self, item, opening_hours):
        if opening_hours:
            oh = OpeningHours()
            try:
                for day, times in zip(DAYS, opening_hours):
                    open, close = times.split(" - ")
                    oh.add_range(day, open.strip(), close.strip())
                item["opening_hours"] = oh
                return
            except:
                self.logger.warning(f"Couldn't parse opening hours: {opening_hours}")
        item["opening_hours"] = None

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
            self.parse_hours(item, poi.get("worktime"))
            apply_yes_no(Extras.WIFI, item, "wifi" in poi["categories"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, "mcdrive" in poi["categories"])
            apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "amex" in poi["categories"])
            apply_yes_no(PaymentMethods.MASTER_CARD, item, "mastercard" in poi["categories"])
            apply_yes_no(PaymentMethods.VISA, item, "visa" in poi["categories"])
            # TODO: other payment methods include:
            #  chequedejeuner club cup darkove doxx edenred eur gastropass isic master nasestravenkaa ticket usd visael

            if "mccafe" in poi["categories"]:
                mccafe = item.deepcopy()
                mccafe["ref"] = "{}-mccafe".format(item["ref"])
                mccafe["brand"] = "McCafé"
                mccafe["brand_wikidata"] = "Q3114287"
                apply_category(Categories.CAFE, mccafe)
                self.parse_hours(mccafe, poi.get("mccafe_worktime"))
                yield mccafe

            yield item
