from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, Fuel, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

ZA_PROVINCES = [
    "Eastern Cape",
    "Free State",
    "Gauteng",
    "KwaZulu-Natal",
    "Limpopo",
    "Mpumalanga",
    "North West",
    "Northern Cape",
    "Western Cape",
]


class SasolZASpider(Spider):
    name = "sasol_za"
    item_attributes = {
        "brand": "Sasol",
        "brand_wikidata": "Q905998",
        "extras": Categories.FUEL_STATION.value,
    }
    allowed_domains = ["locator.sasol.com"]
    start_urls = ["https://locator.sasol.com/api/station.json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stations"]:
            item = DictParser.parse(location)
            item["ref"] = location.pop("station_id")
            item["branch"] = location.pop("station_name").replace(self.item_attributes["brand"], "").strip()
            item["website"] = "https://locator.sasol.com/#/station/" + item["ref"]
            item["addr_full"] = location.pop("station_address")
            try:
                int(item["addr_full"].split(", ")[-1])
                item["postcode"] = item["addr_full"].split(", ")[-1]
            except ValueError:
                pass
            try:
                int(item["addr_full"].split(" ")[0])
                item["housenumber"] = item["addr_full"].split(" ")[0]
                item["street"] = item["addr_full"].split(",")[0].replace(item["housenumber"], "").strip()
            except ValueError:
                pass
            try:
                if item["addr_full"].split(", ")[-2] in ZA_PROVINCES:
                    item["state"] = item["addr_full"].split(", ")[-2]
                    item["city"] = item["addr_full"].split(", ")[-3]
            except IndexError:
                pass
            yield JsonRequest(
                url=f"https://locator.sasol.com/api/station/{item['ref']}.json",
                meta={"item": item},
                callback=self.parse_item,
            )

    def parse_item(self, response):
        item = response.meta["item"]
        location = response.json()

        oh = OpeningHours()
        for days_hours in location["opening_times"]:
            oh.add_ranges_from_string(days_hours["days"] + " " + days_hours["times"])
        item["opening_hours"] = oh.as_opening_hours()

        # Products available at https://locator.sasol.com/api/product.json
        for product in location["products"]:
            if product["product_name"] == "Cash":
                apply_yes_no(Extras.ATM, item, len(product["subproducts"]) > 0)
            if product["product_name"] == "Other":
                apply_yes_no(
                    Extras.TOILETS, item, "Restrooms" in [i["subproduct_name"] for i in product["subproducts"]]
                )
            elif product["product_name"] == "Fuel":
                fuels = [i["subproduct_name"] for i in product["subproducts"]]
                apply_yes_no(Fuel.OCTANE_93, item, "ULP 93" in fuels, False)
                apply_yes_no(Fuel.OCTANE_95, item, "ULP 95" in fuels, False)
                apply_yes_no(Fuel.LPG, item, "LPG" in fuels or "LP Gas" in fuels, False)
                apply_yes_no(
                    Fuel.DIESEL, item, "ULS 10ppm" in fuels or "ULS 50ppm" in fuels or "Turbo Diesel" in fuels, False
                )
                # Unhandled: LRP 95, Paraffin -IP

        yield item
