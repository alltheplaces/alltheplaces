from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.vapestore_gb import clean_address


class BEEVGBSpider(Spider):
    name = "beev_gb"
    item_attributes = {"brand": "Be.EV", "brand_wikidata": "Q118263083"}
    start_urls = ["https://be-ev.co.uk/api/chargepoints/GetSiteMarkersNoFilter"]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = clean_address(
                [location["Address"]["Line1"], location["Address"]["Line2"], location["Address"]["Line3"]]
            )
            if location["OpeningTimes"]["Is24Hours"]:
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"] = OpeningHours()
                for day in DAYS_FULL:
                    rule = location["OpeningTimes"]["Times"].get(day)
                    if not rule:
                        continue
                    if rule["starthours"] != "-1" and rule["endhours"] != "-1":
                        item["opening_hours"].add_range(
                            day, rule["starthours"].zfill(4), rule["endhours"].zfill(4), time_format="%H%M"
                        )
            # TODO: count location["ChargePoints"]?
            # apply_yes_no(Extras.FEE, item, not location["Tariff"]["IsFree"], False)
            # item["extras"]["charge"] = location["Tariff"]["Price"]
            apply_category(Categories.CHARGING_STATION, item)
            yield item
