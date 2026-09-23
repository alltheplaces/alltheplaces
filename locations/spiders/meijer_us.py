import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT

DEPARTMENTS = {
    "BAKERY": None,
    "CURBSIDE": None,
    "DELI": None,
    "DELIVERY": None,
    "GAS": Categories.FUEL_STATION,
    "PHARMACY": Categories.PHARMACY,
    "PHARMACY_DRIVE": None,
}


class MeijerUSSpider(SitemapSpider):
    name = "meijer_us"
    item_attributes = {"brand": "Meijer", "brand_wikidata": "Q1917753"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    sitemap_urls = ["https://www.meijer.com/bin/meijer/store-sitemap.xml"]
    allowed_domains = ["www.meijer.com"]
    store_url = re.compile(r"https://www\.meijer\.com/shopping/store-locator/(\d+)\.html")

    # Only use the sitemap to get a list of store IDs. Get the actual store info from the API.
    def sitemap_filter(self, entries):
        for entry in entries:
            if match := self.store_url.match(entry["loc"]):
                store_id = match.group(1)
                yield {"loc": f"https://www.meijer.com/bin/meijer/store/details?storeId={store_id}"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()
        item = DictParser.parse(location)
        item["country"], item["state"] = location["address"]["region"]["isocode"].split("-")
        item["branch"] = location["displayName"]
        item["ref"] = item["extras"]["ref:meijer"] = item.pop("name")
        item["website"] = f"https://www.meijer.com/shopping/store-locator/{item['ref']}.html"

        item["opening_hours"] = self.parse_opening_hours(location["openingHours"])

        for dept in location["storeLocatorFeatures"]:
            cat = DEPARTMENTS.get(dept["storeFeatureServiceType"])
            if not cat:
                continue

            i = item.deepcopy()
            i["ref"] = "{}-{}".format(dept["storeFeatureServiceType"], i["ref"])

            i["opening_hours"] = self.parse_opening_hours(dept.get("openingSchedule", {}))
            apply_category(cat, i)

            yield i

        apply_yes_no(Extras.DELIVERY, item, location["deliveryEligibility"])
        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours | str:
        if rules["is24Hrsand365Days"]:
            return "24/7"
        else:
            oh = OpeningHours()
            for rule in rules["weekDayOpeningList"]:
                if " - " in rule["weekDay"]:
                    days_range = rule["weekDay"].split(" - ")
                else:
                    days_range = [rule["weekDay"]]
                if rule["closed"]:
                    oh.set_closed(days_range)
                else:
                    oh.add_days_range(
                        days_range,
                        rule["openingTime"]["formattedHour"],
                        rule["closingTime"]["formattedHour"],
                        time_format="%I:%M %p",
                    )
            return oh
