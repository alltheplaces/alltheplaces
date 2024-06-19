from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class DeutschePostDESpider(Spider):
    name = "deutsche_post_de"
    allowed_domains = ["www.deutschepost.de"]
    item_attributes = {"brand": "Deutsche Post", "brand_wikidata": "Q157645"}
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}

    cats = {
        "PAKETBOX": None,
        "PACKSTATION": Categories.PARCEL_LOCKER,
        "LETTER_BOX": Categories.POST_BOX,
        "STAMP_DISPENSER": None,
        "CASH_MACHINE": Categories.ATM,
        "STATEMENT_PRINTER": None,
        "POSTBANK_FINANCE_CENTER": None,
        "RETAIL_OUTLET": Categories.POST_OFFICE,
        "PAKETSHOP": None,
        "SELLING_POINT": None,
        "BULK_ACCEPTANCE_OFFICE": None,
        "BUSINESS_MAIL_ACCEPTANCE_POINT": None,
        "POST_OFFICE_BOX": Categories.POST_BOX,
        "POSTSTATION": None,
    }

    def start_requests(self):
        for lat, lon in point_locations("germany_grid_15km.csv"):
            yield JsonRequest(
                f"https://www.deutschepost.de/int-postfinder/webservice/rest/v1/nearbySearch?address={lat},{lon}",
                headers={"Sec-Fetch-Dest": "empty"},
            )

    @staticmethod
    def parse_hours(hours: [dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for hour in hours:
            if not hour["type"] == "OPENINGHOUR":
                continue
            if ":" not in hour["timefrom"]:
                continue
            if hour["timefrom"] == "24:00":
                hour["timefrom"] = "23:59"
            opening_hours.add_range(
                day=DAYS[hour["weekday"] - 1], open_time=hour["timefrom"], close_time=hour["timeto"]
            )
        return opening_hours

    def parse(self, response, **kwargs):
        for location in response.json()["pfLocations"]:
            location["location"] = location["geoPosition"]
            item = DictParser.parse(location)
            item["ref"] = location["primaryKeyDeliverySystem"]
            item["name"] = location["locationName"]
            item["state"] = location["district"]
            item["opening_hours"] = self.parse_hours(location["pfTimeinfos"])

            if cat := self.cats.get(location["locationType"]):
                apply_category(cat, item)
            else:
                item["extras"]["type"] = location["locationType"]
                self.crawler.stats.inc_value(f'atp/deutsche_post_de/unmapped_category/{location["locationType"]}')

            yield item
