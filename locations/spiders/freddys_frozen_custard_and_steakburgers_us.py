from datetime import timedelta, date

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class FreddysFrozenCustardAndSteakburgersSpider(Spider):
    name = "freddys_frozen_custard_and_steakburgers_us"
    item_attributes = {"brand": "Freddy's Frozen Custard & Steakburgers", "brand_wikidata": "Q5496837"}
    allowed_domains = ["www.freddys.com"]
    start_urls = ["https://www.freddys.com/restaurants/"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def start_requests(self):
        from_date = date.today().strftime("%Y%m%d")
        to_date = (date.today() + timedelta(days=7)).strftime("%Y%m%d")
        for url in self.start_urls:
            yield JsonRequest(url=f"{url}?nomnom=calendars&nomnom_calendars_from={from_date}&nomnom_calendars_to={to_date}")

    def parse(self, response):
        for location in response.json()["restaurants"]:
            if not location["isavailable"]:
                continue
            item = DictParser.parse(location)
            item["opening_hours"] = OpeningHours()
            for day_hours in location["calendars"]["calendar"][0]["ranges"]:
                item["opening_hours"].add_range(day_hours["weekday"], day_hours["start"].split(" ", 1)[1], day_hours["end"].split(" ", 1)[1])
            apply_yes_no(Extras.DELIVERY, item, location["candeliver"], False)
            apply_yes_no(Extras.TAKEAWAY, item, location["canpickup"], False)
            apply_yes_no(Extras.INDOOR_SEATING, item, location["supportsdinein"], False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["supportsdrivethru"], False)
            apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "American Express" in location["supportedcardtypes"], False)
            apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "Discover" in location["supportedcardtypes"], False)
            apply_yes_no(PaymentMethods.MASTER_CARD, item, "MasterCard" in location["supportedcardtypes"], False)
            apply_yes_no(PaymentMethods.VISA, item, "Visa" in location["supportedcardtypes"], False)
            yield item
