from urllib.parse import urljoin

from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.asda_gb import AsdaGBSpider
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.spiders.vets4pets_gb import set_located_in
from locations.user_agents import FIREFOX_LATEST


class KfcGBSpider(Spider):
    name = "kfc_gb"
    item_attributes = KFC_SHARED_ATTRIBUTES
    start_urls = ["https://uk.kfc-cms.com/api/data/restaurants_all?countrycode=GB"]
    user_agent = FIREFOX_LATEST
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def parse(self, response, **kwargs):
        for location in response.json():
            if location["status"] != "available":
                continue

            location["street_address"] = location.pop("street")
            location["id"] = location.pop("storeid")

            item = DictParser.parse(location)
            if slug := location.get("link"):
                item["website"] = urljoin("https://www.kfc.co.uk/", slug)

            if item.get("state") in ["Unknown", "Other", "Republic of Ireland"]:
                item["state"] = None

            for h in location["hours"]:
                if h["type"] == "Standard":
                    item["opening_hours"] = self.parse_opening_hours(h)
                elif h["type"] == "Drivethru":
                    item["extras"]["opening_hours:drive_through"] = self.parse_opening_hours(h).as_opening_hours()

            facilities = [f["name"] for f in location["facilities"]]
            apply_yes_no(Extras.WHEELCHAIR, item, "Disability Access" in facilities)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in facilities)
            apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "Baby Changing Room" in facilities)
            apply_yes_no(Extras.WIFI, item, "Free Wifi" in facilities)

            if "ASDA" in item["name"].upper():
                set_located_in(item, AsdaGBSpider.item_attributes)

            item["branch"] = item.pop("name")

            yield item

    def parse_opening_hours(self, rules: [dict]) -> OpeningHours:
        oh = OpeningHours()

        for d in DAYS_FULL:
            day = rules[d.lower()]
            if day["open"] == 0:
                day["open"] = "0000"
            if day["close"] == 0:
                day["close"] = "2359"

            oh.add_range(d, str(day["open"]).zfill(4), str(day["close"]).zfill(4), time_format="%H%M")
        return oh
