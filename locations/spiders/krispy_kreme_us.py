from scrapy import Spider

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class KrispyKremeUSSpider(Spider):
    name = "krispy_kreme_us"
    item_attributes = {"brand": "Krispy Kreme", "brand_wikidata": "Q1192805", "extras": Categories.FAST_FOOD.value}
    allowed_domains = ["api.krispykreme.com"]
    start_urls = [
        "https://api.krispykreme.com/shops/?latitude=41.1199&longitude=-74.1242&count=10000&shopFeatureFlags=0&includeGroceryStores=false&includeShops=true"
    ]

    def parse(self, response):
        for location in response.json():
            if location.get("isClosed"):
                continue

            item = DictParser.parse(location)
            item["ref"] = location["shopId"]
            item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
            item["website"] = location.get("pagesUrl")
            item["facebook"] = location.get("facebookPageUrl")

            hours_text = " ".join(
                ["{}: {}".format(day_hours["key"], day_hours["value"]) for day_hours in location["hoursDineIn"]]
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text)

            apply_yes_no(Extras.DELIVERY, item, location.get("canDeliver"), False)
            apply_yes_no(
                Extras.DRIVE_THROUGH,
                item,
                location.get("hoursDriveThru")[0]["key"] != "Not Available at this Location",
                False,
            )

            yield item
