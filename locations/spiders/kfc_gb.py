from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.asda import AsdaSpider
from locations.spiders.kfc import KFCSpider
from locations.spiders.vets4pets_gb import set_located_in
from locations.user_agents import BROWSER_DEFAULT


class KFCGB(Spider):
    name = "kfc_gb"
    item_attributes = KFCSpider.item_attributes
    start_urls = ["https://www.kfc.co.uk/cms/api/data/restaurants_all"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response, **kwargs):
        for location in response.json():
            if location["status"] != "available":
                continue

            location["street_address"] = location.pop("street")
            location["id"] = location.pop("storeid")

            item = DictParser.parse(location)

            item["website"] = "https://www.kfc.co.uk" + location["link"]

            for h in location["hours"]:
                if h["type"] == "Standard":
                    oh = OpeningHours()

                    for d in DAYS_FULL:
                        day = h[d.lower()]
                        if day["open"] == 0:
                            day["open"] = "0000"
                        if day["close"] == 0:
                            day["close"] = "2359"

                        oh.add_range(d, str(day["open"]).zfill(4), str(day["close"]).zfill(4), time_format="%H%M")

                    item["opening_hours"] = oh.as_opening_hours()
                    break

            apply_yes_no(
                Extras.WHEELCHAIR, item, any(f["name"] == "Disability Access" for f in location["facilities"]), False
            )
            apply_yes_no(
                Extras.DRIVE_THROUGH, item, any(f["name"] == "Drive Thru" for f in location["facilities"]), False
            )
            apply_yes_no(
                Extras.BABY_CHANGING_TABLE,
                item,
                any(f["name"] == "Baby Changing Room" for f in location["facilities"]),
                False,
            )
            apply_yes_no(Extras.WIFI, item, any(f["name"] == "Free Wifi" for f in location["facilities"]), False)

            if "ASDA" in item["name"].upper():
                set_located_in(item, AsdaSpider.item_attributes)

            yield item
