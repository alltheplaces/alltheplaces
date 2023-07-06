import scrapy
from scrapy import Request

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.costacoffee_gb import yes_or_no


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
            item["extras"]["atm"] = yes_or_no(any(f["id"] == 2 for f in store["facilities"]))
            item["extras"]["sells:national_lottery"] = yes_or_no(any(f["id"] == 6 for f in store["facilities"]))
            item["extras"]["car_wash"] = yes_or_no(any(f["id"] == 30 for f in store["facilities"]))
            item["extras"]["wheelchair"] = yes_or_no(any(f["id"] == 162 for f in store["facilities"]))

            if any(f["id"] == 28 for f in store["facilities"]):
                item["extras"]["has_parking"] = "yes"

                item["extras"]["parking:capacity:disabled"] = yes_or_no(
                    any(f["id"] == 166 for f in store["facilities"])
                )
                item["extras"]["parking:capacity:parent"] = yes_or_no(any(f["id"] == 167 for f in store["facilities"]))

            item["extras"]["toilets"] = yes_or_no(any(f["id"] == 16 for f in store["facilities"]))
            item["extras"]["changing_table"] = yes_or_no(any(f["id"] == 169 for f in store["facilities"]))
            item["extras"]["toilets:wheelchair"] = yes_or_no(any(f["id"] == 9 for f in store["facilities"]))

            if any(f["id"] == 221 for f in store["facilities"]):
                item["extras"]["internet_access"] = "wlan"
                item["extras"]["internet_access:fee"] = "no"

            item["extras"]["self_checkout"] = yes_or_no(
                any(f["id"] == 4 or f["id"] == 224 for f in store["facilities"])
            )
            item["extras"]["payment:contactless"] = yes_or_no(any(f["id"] == 104 for f in store["facilities"]))
            item["extras"]["paypoint"] = yes_or_no(any(f["id"] == 231 for f in store["facilities"]))

            if store["store_type"] == "local":
                item.update(self.SAINSBURYS_LOCAL)
                item["extras"]["shop"] = "convenience"
            elif store["store_type"] == "main":
                item["extras"]["shop"] = "supermarket"

                item["extras"]["key_cutting"] = yes_or_no(any(f["id"] == 32 for f in store["facilities"]))
            elif store["store_type"] == "argos":
                continue  # ArgosSpider
            elif store["store_type"] == "pfs":
                item["extras"]["amenity"] = "fuel"

                item["extras"]["fuel:diesel"] = yes_or_no(any(f["id"] == 17 for f in store["facilities"]))
                item["extras"]["fuel:electric"] = yes_or_no(any(f["id"] == 108 for f in store["facilities"]))
                item["extras"]["fuel:lpg"] = yes_or_no(any(f["id"] == 192 for f in store["facilities"]))
                item["extras"]["fuel:super_unleaded"] = yes_or_no(any(f["id"] == 34 for f in store["facilities"]))
                item["extras"]["fuel:petrol"] = yes_or_no(any(f["id"] == 11 for f in store["facilities"]))
            elif store["store_type"] == "pharmacy":
                continue  # LloydsPharmacyGBSpider
            elif store["store_type"] == "tm":
                item["extras"]["amenity"] = "bureau_de_change"
            elif store["store_type"] == "specsavers":
                continue  # SpecsaversGBSpider
            elif store["store_type"] == "restaurant":
                item["extras"]["amenity"] = "cafe"
            elif store["store_type"] == "habitat":
                continue  # https://www.habitat.co.uk/
            else:
                item["extras"]["type"] = store["store_type"]

            yield item

        yield Request(
            url=f'{self.start_urls[0]}&offset={str(int(data["page_meta"]["offset"] + data["page_meta"]["limit"]))}'
        )
