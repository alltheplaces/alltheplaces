import re

from scrapy import Request, Spider

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class WegmansUSSpider(Spider):
    name = "wegmans_us"
    item_attributes = {"brand": "Wegmans", "brand_wikidata": "Q11288478", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["shop.wegmans.com", "www.wegmans.com"]
    start_urls = ["https://shop.wegmans.com/api/v2/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for location in response.json()["items"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name", None)
            item["street_address"] = clean_address(
                [
                    location["address"].get("address1"),
                    location["address"].get("address2"),
                    location["address"].get("address3"),
                ]
            )
            if location.get("amenities"):
                apply_yes_no(Extras.WIFI, item, "Wi-Fi Internet Access" in location["amenities"], False)
            apply_yes_no(Extras.DELIVERY, item, location.get("has_delivery") is True, False)
            if location.get("external_url"):
                item["website"] = location["external_url"]
                if item["website"][-1] != "/":
                    item["website"] = item["website"] + "/"
                yield Request(url=item["website"], meta={"item": item}, callback=self.parse_opening_hours)
            else:
                yield item

    def parse_opening_hours(self, response):
        item = response.meta["item"]
        hours_string = response.xpath('//div[@id="storeHoursID"]/text()').get("").strip().replace("Midnight", "11:59PM")
        if m := re.match(
            r"Open (\d{1,2}(?:\:\d{2})?\s*AM) to (\d{1,2}(?:\:\d{2})?\s*PM)\s*,\s*7 Days a Week",
            hours_string,
            flags=re.IGNORECASE,
        ):
            item["opening_hours"] = OpeningHours()
            open_time = re.sub(r"\s+", "", m.group(1))
            if ":" not in open_time:
                open_time = open_time.replace("AM", ":00AM").replace("PM", ":00PM")
            close_time = re.sub(r"\s+", "", m.group(2))
            if ":" not in close_time:
                close_time = close_time.replace("AM", ":00AM").replace("PM", ":00PM")
            item["opening_hours"].add_days_range(DAYS, open_time, close_time, "%I:%M%p")
        yield item
