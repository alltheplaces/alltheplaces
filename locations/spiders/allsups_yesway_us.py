import scrapy

from locations.categories import Extras, Fuel, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class AllsupsYeswayUSSpider(scrapy.Spider):
    name = "allsups_yesway_us"
    allowed_domains = ["allsups.com"]
    start_urls = [
        "https://allsups.com/wp-json/acf/v3/business_locations?_embed&per_page=1000",
    ]

    BRANDS = {
        "Allsup's": {"brand": "Allsup's", "brand_wikidata": "Q4733292"},
        "Yesway": {"brand": "Yesway", "brand_wikidata": "Q75851666"},
    }

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store["acf"])
            item["ref"] = store["acf"]["internal_store_code"]
            item["phone"] = store["acf"]["primary_phone"]
            item["street_address"] = merge_address_lines(
                [store["acf"]["address_line_1"], store["acf"]["address_line_2"]]
            )

            if brand := self.BRANDS.get(store["acf"]["business_name"]):
                item.update(brand)

            apply_yes_no(Extras.ATM, item, "atm" in store["acf"]["amenities"])
            apply_yes_no(Extras.CAR_WASH, item, "car_wash" in store["acf"]["amenities"])
            apply_yes_no(Fuel.DIESEL, item, "diesel_fuel" in store["acf"]["amenities"])
            apply_yes_no(Fuel.E85, item, "e85_fuel" in store["acf"]["amenities"])

            if "twenty_four_hour" in store["acf"]["amenities"]:
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"] = OpeningHours()
                for day in DAYS_FULL:
                    if times := store["acf"].get(day.lower(), "").replace(" - ", "-"):
                        item["opening_hours"].add_range(day, *times.split("-"), time_format="%I:%M%p")

            yield item
