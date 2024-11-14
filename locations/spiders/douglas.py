from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class DouglasSpider(Spider):
    name = "douglas"
    item_attributes = {
        "brand": "Douglas",
        "brand_wikidata": "Q2052213",
    }
    user_agent = BROWSER_DEFAULT
    requires_proxy = "DE"

    def start_requests(self):
        for tld in ("at", "be", "ch", "de", "es", "it", "nl", "pl"):
            yield Request(
                f"https://www.douglas.{tld}/api/v2/stores?fields=FULL&pageSize=1000&sort=asc",
                headers={
                    # Need to make the requests more browser-like
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.8",
                },
            )

    def parse(self, response, **kwargs):
        for feature in response.json()["stores"]:
            feature["ref"] = feature.pop("name")
            if "displayName" in feature:
                feature["branch"] = feature.pop("displayName")
            else:
                feature["branch"] = feature["address"]["town"] + ", " + feature["address"]["line1"]
            if "address" in feature:
                feature["address"]["house_number"] = feature["address"].get("line2")
                feature["address"]["country"] = feature["address"]["country"]["isocode"]
                if "region" in feature["address"]:
                    feature["address"]["region"] = feature["address"]["region"]["isocodeShort"]
            feature["website"] = response.urljoin(feature.pop("url"))
            item = DictParser().parse(feature)
            item["opening_hours"] = self.parse_opening_hours(feature["openingHours"]["weekDayOpeningList"])
            apply_category(Categories.SHOP_PERFUMERY, item)
            if item["lat"] is not None and item["lon"] is not None:
                yield item

    def parse_opening_hours(self, opening_list):
        hours = OpeningHours()
        days_zero_based = ["Su"] + DAYS
        for day_definition in opening_list:
            if "openingTime" in day_definition:
                hours.add_range(
                    days_zero_based[day_definition["dayOfWeek"]],
                    day_definition["openingTime"]["formattedHour"],
                    day_definition["closingTime"]["formattedHour"],
                )
        return hours
