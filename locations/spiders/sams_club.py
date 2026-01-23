from scrapy import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SamsClubSpider(Spider):
    name = "sams_club"
    item_attributes = {"brand": "Sam's Club", "brand_wikidata": "Q1972120"}
    start_urls = [
        "https://www.samsclub.com/api/node/vivaldi/browse/v2/clubfinder/list?singleLineAddr=USA&distance=50000&nbrOfStores=1000"
    ]

    def parse(self, response):
        for store in response.json():
            if store.get("clubAttributes", {}).get("isDeleted") or store.get("clubAttributes", {}).get(
                "isTemporarilyClosed"
            ):
                continue

            store.update(store.pop("address", {}))
            store.update(store.pop("geoPoint", {}))
            store["street_address"] = store.get("address1")
            item = DictParser.parse(store)
            item["website"] = f"https://www.samsclub.com/club/{store['id']}"

            services = store.get("services", [])

            if gas_prices := store.get("gasPrices"):
                fuel_station = item.deepcopy()
                fuel_station["ref"] = f"{store['id']}_fuel"
                fuel_station["extras"] = {}
                fuel_types = {fuel["name"] for fuel in gas_prices}
                apply_yes_no(Fuel.OCTANE_87, fuel_station, "UNLEAD" in fuel_types)
                apply_yes_no(Fuel.OCTANE_89, fuel_station, "MIDGRAD" in fuel_types or "MID CLR" in fuel_types)
                apply_yes_no(Fuel.OCTANE_91, fuel_station, "PREMIUM" in fuel_types or "PREM CLR" in fuel_types)
                apply_yes_no(Fuel.DIESEL, fuel_station, "DIESEL" in fuel_types)
                apply_category(Categories.FUEL_STATION, fuel_station)
                yield fuel_station

            club_attrs = store.get("clubAttributes", {})
            apply_yes_no(Extras.TYRE_SERVICES, item, "tires_&_batteries" in services)
            apply_yes_no(Extras.SELF_CHECKOUT, item, club_attrs.get("isScanNGo"))
            apply_yes_no(Extras.DELIVERY, item, club_attrs.get("isClubEnabledForRegularDelivery"))
            item["opening_hours"] = self.parse_hours(store.get("operationalHours", {}))

            apply_category(Categories.SHOP_WHOLESALE, item)

            yield item

    def parse_hours(self, hours_data: dict) -> OpeningHours:
        oh = OpeningHours()
        if mon_fri := hours_data.get("monToFriHrs"):
            for day in ["Mo", "Tu", "We", "Th", "Fr"]:
                oh.add_range(day, mon_fri["startHrs"], mon_fri["endHrs"])
        if sat := hours_data.get("saturdayHrs"):
            oh.add_range("Sa", sat["startHrs"], sat["endHrs"])
        if sun := hours_data.get("sundayHrs"):
            oh.add_range("Su", sun["startHrs"], sun["endHrs"])
        return oh
