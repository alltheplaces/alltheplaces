import re
from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines

TIME_RANGE_REGEX = re.compile(r"(\d{1,2}:\d{2}[AP]M) - (\d{1,2}:\d{2}[AP]M)")
SUB_TENANTS = {
    "pieFace": ({"brand": "Pie Face", "brand_wikidata": "Q18166370"}, Categories.COFFEE_SHOP),
    "quickStop": ({"brand": "Quick Stop", "name": "Quick Stop"}, Categories.SHOP_CONVENIENCE),
}


class UnitedPetroleumAUSpider(Spider):
    name = "united_petroleum_au"
    # Note on brand: some locations are labelled as "Astron Rural"
    # in the source data, but almost all of them show on street view
    # imagery as having "United" branding. It does not appear to be
    # possible to determine whether a location is "Astron" or
    # "United" branded, but in all but seemingly < 5 cases, United
    # is almost always used.
    UNITED = {"brand": "United", "brand_wikidata": "Q28224393"}
    allowed_domains = ["servicestations.unitedpetroleum.com.au"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://servicestations.unitedpetroleum.com.au/api/find",
            data={
                "brand": [],
                "facilitiesAndServices": [],
                "foodAndDrinks": [],
                "fuelCards": [],
                "fuels": [],
                "lat": -37.8585540736312,
                "lon": 145.02824508187487,
                "range": 20000,
                "supermarketVouchers": [],
                "truckFriendly": [],
            },
        )

    @staticmethod
    def parse_opening_hours(hours: dict) -> OpeningHours:
        oh = OpeningHours()
        if hours.get("alwaysOpen"):
            oh.add_days_range(DAYS_FULL, "00:00", "23:59")
            return oh
        for day_name in DAYS_FULL:
            day_hours = hours.get(day_name.lower())
            if hours.get(f"closedOn{day_name}"):
                oh.set_closed(day_name)
            elif hours.get(f"open24Hours{day_name}"):
                # A 24 hour flag beside a time range is contradictory, so the day is left out.
                if not day_hours:
                    oh.add_range(day_name, "00:00", "23:59")
            elif match := TIME_RANGE_REGEX.fullmatch(day_hours or ""):
                try:
                    oh.add_range(day_name, match.group(1), match.group(2), "%I:%M%p")
                except ValueError:
                    pass  # An impossible time such as "10:99AM" leaves only that day out.
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["addr_full"] = merge_address_lines([location["address1"], location["address2"], location["address3"]])

            if food_and_drinks := location.get("foodAndDrinks"):
                for tenant_key, (brand, cat) in SUB_TENANTS.items():
                    if food_and_drinks.get(tenant_key) is True:
                        tenant = item.deepcopy()
                        tenant["name"] = None
                        tenant["ref"] = "{}-{}".format(item["ref"], tenant_key)
                        tenant.update(brand)
                        apply_category(cat, tenant)
                        yield tenant

            if location["brand"] == "united":
                item.update(self.UNITED)
            item["website"] = urljoin("https://servicestations.unitedpetroleum.com.au/location/", location["slug"])
            item["phone"] = location["publicPhoneNumber"]
            item["opening_hours"] = self.parse_opening_hours(location["openingHours"])
            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.OCTANE_98, item, location["fuels"]["premium98"], False)
            apply_yes_no(Fuel.OCTANE_95, item, location["fuels"]["premiumULP"], False)
            apply_yes_no(Fuel.E10, item, location["fuels"]["plus"], False)
            apply_yes_no(Fuel.E85, item, location["fuels"]["e85"], False)
            apply_yes_no(Fuel.DIESEL, item, location["fuels"]["predis"] or location["fuels"]["diesel"], False)
            apply_yes_no(Fuel.LPG, item, location["fuels"]["lpg"], False)
            apply_yes_no(Fuel.ADBLUE, item, location["fuels"]["adblue"], False)
            apply_yes_no(Fuel.PROPANE, item, location["facilitiesAndServices"]["bbqGas"], False)
            apply_yes_no(Extras.TOILETS, item, location["facilitiesAndServices"]["toilets"], False)
            apply_yes_no(Extras.SHOWERS, item, location["facilitiesAndServices"]["showers"], False)
            apply_yes_no(Extras.ATM, item, location["facilitiesAndServices"]["atm"], False)
            apply_yes_no(Extras.CAR_WASH, item, location["facilitiesAndServices"].get("carWash"))

            yield item
