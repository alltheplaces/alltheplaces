from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class LAndLHawaiianBarbecueUSSpider(Spider):
    name = "l_and_l_hawaiian_barbecue_us"
    item_attributes = {
        "brand": "L&L Hawaiian Barbecue",
        "brand_wikidata": "Q6455441",
        "extras": Categories.FAST_FOOD.value | {"cuisine": "hawaiian", Extras.TAKEAWAY.value: "yes"},
    }
    start_urls = ["https://www.hawaiianbarbecue.com/page-data/locations/page-data.json"]

    def parse(self, response):
        for q in response.json()["staticQueryHashes"]:
            yield JsonRequest(
                f"https://www.hawaiianbarbecue.com/page-data/sq/d/{q}.json", callback=self.parse_locations
            )

    def parse_locations(self, response):
        for location in response.json().get("data", {}).get("allPrismicLocation", {}).get("nodes", []):
            if "uid" not in location:
                continue

            item = DictParser.parse(
                {
                    k: list(v.values())[0] if isinstance(v, dict) and len(v) == 1 else v
                    for k, v in location["data"].items()
                }
            )
            item["ref"] = location["uid"]
            item["website"] = response.urljoin(location["url"])
            item["branch"] = item.pop("name")
            item["name"] = item["brand"] = location["data"]["type"]
            item["extras"]["website:menu"] = (location["data"]["menu"] or {}).get("url")
            apply_yes_no(Extras.DELIVERY, item, location["data"]["provides_delivery"])

            oh = OpeningHours()
            for day in DAYS_FULL:
                hours = location["data"][f"{day.lower()}_hours"]["text"]
                oh.add_ranges_from_string(f"{day} {hours}")
            item["opening_hours"] = oh

            yield item
