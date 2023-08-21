import scrapy
from scrapy import Request

from locations.categories import apply_category, apply_yes_no, Categories, Extras, Fuel, PaymentMethods
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class SainsburysSpider(scrapy.Spider):
    name = "sainsburys"
    SAINSBURYS = {"brand": "Sainsbury's", "brand_wikidata": "Q152096"}
    SAINSBURYS_LOCAL = {"brand": "Sainsbury's Local", "brand_wikidata": "Q13218434"}
    item_attributes = SAINSBURYS
    allowed_domains = ["stores.sainsburys.co.uk"]
    start_urls = ["https://stores.sainsburys.co.uk/api/v1/stores?api_client_id=slfe"]

    def parse(self, response):
        data = response.json()

        if len(data["results"]) == 0:
            return

        for store in data["results"]:
            store.update(store.pop("contact"))
            store["id"] = store["code"]

            store["street_address"] = ", ".join(filter(None, [store["address1"], store["address2"]]))

            if store.get("other_name"):
                store["name"] = store["other_name"]

            item = DictParser.parse(store)

            oh = OpeningHours()
            for rule in store["opening_times"]:
                for time in rule["times"]:
                    oh.add_range(DAYS[rule["day"]], time["start_time"], time["end_time"])

            item["opening_hours"] = oh.as_opening_hours()
            item["website"] = "https://stores.sainsburys.co.uk/{}/{}".format(
                item["ref"], item["name"].lower().replace(" ", "-")
            )

            item["extras"] = {}
            item["extras"]["fhrs:id"] = store["fsa_scores"]["fhrs_id"]

            # https://stores.sainsburys.co.uk/api/v1/facilities
            apply_yes_no(Extras.ATM, item, any(f["id"] == 2 for f in store["facilities"]), False)
            apply_yes_no("sells:national_lottery", item, any(f["id"] == 6 for f in store["facilities"]), False)
            apply_yes_no(Extras.CAR_WASH, item, any(f["id"] == 30 for f in store["facilities"]), False)
            apply_yes_no(Extras.WHEELCHAIR, item, any(f["id"] == 162 for f in store["facilities"]), False)
            apply_yes_no(Extras.TOILETS, item, any(f["id"] == 16 for f in store["facilities"]), False)
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, any(f["id"] == 9 for f in store["facilities"]), False)
            apply_yes_no(Extras.BABY_CHANGING_TABLE, item, any(f["id"] == 169 for f in store["facilities"]), False)
            apply_yes_no(Extras.WIFI, item, any(f["id"] == 221 for f in store["facilities"]), False)
            apply_yes_no(Extras.SELF_CHECKOUT, item, any(f["id"] == 4 or f["id"] == 224 for f in store["facilities"]), False)
            if any(f["id"] == 28 for f in store["facilities"]):
                apply_category(Categories.PARKING, item)
                apply_yes_no(Extras.PARKING_PARENT, item, any(f["id"] == 167 for f in store["facilities"]), False)
                apply_yes_no(Extras.PARKING_WHEELCHAIR, item, any(f["id"] == 166 for f in store["facilities"]), False)
            apply_yes_no(PaymentMethods.CONTACTLESS, item, any(f["id"] == 104 for f in store["facilities"]), False)

            if store["store_type"] == "local":
                item.update(self.SAINSBURYS_LOCAL)
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif store["store_type"] == "main":
                apply_category(Categories.SHOP_SUPERMARKET, item)
                if any(f["id"] == 32 for f in store["facilities"]):
                    apply_category(Categories.CRAFT_KEY_CUTTER, item)
            elif store["store_type"] == "argos":
                continue  # ArgosSpider
            elif store["store_type"] == "pfs":
                apply_category(Categories.FUEL_STATION, item)
                if any(f["id"] == 108 for f in store["facilities"]):
                    apply_categoriy(Categories.CHARGING_STATION, item)
                apply_yes_no(Fuel.DIESEL, item, any(f["id"] == 17 for f in store["facilities"]), False)
                apply_yes_no(Fuel.LPG, item, any(f["id"] == 192 for f in store["facilities"]), False)
                apply_yes_no(Fuel.OCTANE_95, any(f["id"] == 11 for f in store["facilities"]), False) # "Petrol"
                apply_yes_no(Fuel.OCTANE_97, any(f["id"] == 34 for f in store["facilities"]), False) # "Super Unleaded"
            elif store["store_type"] == "pharmacy":
                continue  # LloydsPharmacyGBSpider
            elif store["store_type"] == "tm":
                apply_category(Categories.BUREAU_DE_CHANGE, item)
            elif store["store_type"] == "specsavers":
                continue  # SpecsaversGBSpider
            elif store["store_type"] == "restaurant":
                item["extras"]["amenity"] = "cafe"
                apply_category(Categories.CAFE, item)
            elif store["store_type"] == "habitat":
                continue  # https://www.habitat.co.uk/
            else:
                item["extras"]["type"] = store["store_type"]

            yield item

        yield Request(
            url=f'{self.start_urls[0]}&offset={str(int(data["page_meta"]["offset"] + data["page_meta"]["limit"]))}'
        )
