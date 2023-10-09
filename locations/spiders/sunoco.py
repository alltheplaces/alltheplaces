import scrapy

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SunocoUSSpider(scrapy.Spider):
    name = "sunoco_us"
    item_attributes = {"brand": "Sunoco", "brand_wikidata": "Q1423218"}
    allowed_domains = ["sunoco.com"]

    start_urls = ["https://www.sunoco.com/js/locations.json"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["Store_ID"]
            item["postcode"] = str(location["Postalcode"])
            self.parse_hours(item, location)
            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.DIESEL, item, location["HasDiesel"] == "Y")
            apply_yes_no(Fuel.KEROSENE, item, location["HasKero"] == "Y")
            apply_yes_no(Fuel.OCTANE_94, item, location["ultra94"] == "Y")
            apply_yes_no(Extras.ATM, item, location["ATM"] == "Y")
            apply_yes_no(Extras.CAR_WASH, item, location["CarWash"])
            yield item

    def parse_hours(self, item, location):
        oh = OpeningHours()
        try:
            for key, val in location.items():
                if not key.endswith("_Hours"):
                    continue
                day = key[:2].capitalize()
                if val == "Open Today":
                    continue
                if val == "24 hours":
                    open_time = close_time = "12 AM"
                else:
                    open_time, close_time = val.split(" to ")
                oh.add_range(day, open_time, close_time, "%I %p")
            item["opening_hours"] = oh.as_opening_hours()
        except Exception:
            # TODO: we might want to have a common log for failed hours
            self.crawler.stats.inc_value("atp/hours_parsing/failed")
