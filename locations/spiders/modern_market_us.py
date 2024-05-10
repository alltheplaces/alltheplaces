from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class ModernMarketUSSpider(Spider):
    name = "modern_market_us"
    item_attributes = {"brand": "Modern Market", "brand_wikidata": "Q123370165"}
    allowed_domains = ["modernmarket.com"]
    start_urls = ["https://modernmarket.com/api/restaurants"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["restaurants"]:
            if "COMING SOON" in location["name"].upper():
                continue
            item = DictParser.parse(location)
            item["street_address"] = clean_address([location.get("streetaddress"), location.get("streetaddress2")])
            apply_yes_no(Extras.DELIVERY, item, location.get("candeliver"), False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location.get("supportsdrivethru"), False)
            item["opening_hours"] = OpeningHours()
            for calendar in location.get("calendar"):
                if calendar["type"] == "business":
                    if len(calendar["ranges"]) >= 7:
                        for i in range(0, 6, 1):
                            item["opening_hours"].add_range(
                                calendar["ranges"][i]["weekday"],
                                calendar["ranges"][i]["start"].split(" ", 1)[1],
                                calendar["ranges"][i]["end"].split(" ", 1)[1],
                            )
                    break
            apply_category(Categories.RESTAURANT, item)
            yield item
