from html import unescape

from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RepsolPTSpider(Spider):
    name = "repsol_pt"
    item_attributes = {"brand": "Repsol", "brand_wikidata": "Q174747"}
    allowed_domains = ["repsolmove.com"]
    start_urls = ["https://repsolmove.com/localizador-es"]

    def parse(self, response):
        js_blob = unescape(response.xpath('//service-station-map/@*[name()=":initial-data"]').get())
        for location in parse_js_object(js_blob):
            item = DictParser.parse(location)
            item["lat"] = location["coordinates"]["y"]
            item["lon"] = location["coordinates"]["x"]
            item["street_address"] = item.pop("addr_full", None)
            item["opening_hours"] = OpeningHours()
            for day_hours in location["timetable"]:
                times = day_hours["hours"].split(", ", 3)
                item["opening_hours"].add_range(day_hours["day"].title(), times[0], times[1], "%H:%M:%S")
                item["opening_hours"].add_range(day_hours["day"].title(), times[2], times[3], "%H:%M:%S")
            apply_category(Categories.FUEL_STATION, item)
            fuel_types = [fuel_type["text"] for fuel_type in location.get("products", [])]
            if len(fuel_types) > 0:
                apply_yes_no(Fuel.OCTANE_91, item, "Gasóleo" in fuel_types, False)
                apply_yes_no(
                    Fuel.OCTANE_95,
                    item,
                    "Gasolina Efitec 95" in fuel_types
                    or "Gasolina S/Chumbo 95" in fuel_types
                    or "Ef 95 Premium" in fuel_types,
                    False,
                )
                apply_yes_no(Fuel.OCTANE_98, item, "Gasolina Efitec 98" in fuel_types, False)
                apply_yes_no(
                    Fuel.DIESEL, item, "Repsol Diesel E+ 10" in fuel_types or "AGRODIESEL e+10" in fuel_types, False
                )
                apply_yes_no(Fuel.BIODIESEL, item, "Diesel 100% Renovável" in fuel_types, False)
                apply_yes_no(Fuel.LPG, item, "Autogás" in fuel_types, False)
                apply_yes_no(Fuel.ADBLUE, item, "Adblue Granel" in fuel_types, False)
            yield item
