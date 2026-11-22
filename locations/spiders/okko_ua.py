import re

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider

FUELS = {
    "A95_EVRO": Fuel.OCTANE_95,
    "Pulls95": Fuel.OCTANE_95,
    "Pulls100": Fuel.OCTANE_100,
    "DP_EVRO": Fuel.DIESEL,
    "Pulls_Diesel": Fuel.DIESEL,
    "Gas": Fuel.LPG,
    "adblue": Fuel.ADBLUE,
}
SERVICES = {
    "SwappingWheel": Extras.COMPRESSED_AIR,
    "VacuumCleaner": Extras.VACUUM_CLEANER,
    "Inclusive_WC": Extras.TOILETS_WHEELCHAIR,
    "Pelenalny_stolyk": Extras.BABY_CHANGING_TABLE,
}


class OkkoUASpider(JSONBlobSpider):
    name = "okko_ua"
    item_attributes = {"brand": "ОККО", "brand_wikidata": "Q2045483"}
    start_urls = ["https://www.okko.ua/api/uk/type/gas_stations"]
    locations_key = "collection"

    def pre_process_data(self, feature):
        feature.update(feature.pop("attributes"))

    def post_process_item(self, item, response, feature):
        item["ref"] = feature["Cod_AZK"]
        item["street_address"] = feature["Adresa"].partition("АЗК №")[0]
        item["city"] = feature["Naselenyy_punkt"]

        schedule = re.search(r"Графік роботи АЗК: (цілодобово|з (\d+:\d\d) до (\d+:\d\d))", feature["Work_schedule"])
        if schedule:
            item["opening_hours"] = OpeningHours()
            if schedule.group(2):
                item["opening_hours"].add_days_range(DAYS, schedule.group(2), schedule.group(3))
            else:
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")

        codes = {
            service["attributes"]["code"]
            for key in ("fuel_type", "other_services", "car_services")
            for service in feature[key]
        }
        for code, tag in {**FUELS, **SERVICES}.items():
            apply_yes_no(tag, item, code in codes)
        apply_yes_no(Extras.CAR_WASH, item, bool(feature["car_washes"]))

        apply_category(Categories.FUEL_STATION, item)
        yield item
