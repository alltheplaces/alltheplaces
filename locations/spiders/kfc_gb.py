from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.asda import AsdaSpider
from locations.spiders.costacoffee_gb import yes_or_no
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

                        oh.add_range(
                            d, str(day["open"]), str(day["close"]), time_format="%H%M"
                        )

                    item["opening_hours"] = oh.as_opening_hours()
                    break

            item["extras"] = {
                "wheelchair": yes_or_no(
                    any(
                        f["name"] == "Disability Access" for f in location["facilities"]
                    )
                ),
                "drive_through": yes_or_no(
                    any(f["name"] == "Drive Thru" for f in location["facilities"])
                ),
                "changing_table": yes_or_no(
                    any(
                        f["name"] == "Baby Changing Room"
                        for f in location["facilities"]
                    )
                ),
            }

            if any(f["name"] == "Free Wifi" for f in location["facilities"]):
                item["extras"]["internet_access"] = "wlan"
                item["extras"]["internet_access:fee"] = "no"

            if "ASDA" in item["name"].upper():
                set_located_in(item, AsdaSpider.item_attributes)

            yield item
