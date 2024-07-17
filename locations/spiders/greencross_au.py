from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class GreencrossAUSpider(Spider):
    name = "greencross_au"
    allowed_domains = ["www.petbarn.com.au"]
    start_urls = ["https://www.petbarn.com.au/store-finder/index/dataAjax/?types=pb%2Cgx%2Ccf"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            properties = {
                "ref": location["i"],
                "name": location["n"],
                "lat": location["l"],
                "lon": location["g"],
                "street_address": clean_address(location["a"][0 : len(location["a"]) - 3]),
                "city": location["a"][-3],
                "state": location["a"][-2],
                "postcode": location["a"][-1],
                "email": location["e"],
                "phone": location["p"],
                "website": "https://www.petbarn.com.au" + location["u"],
                "nsi_id": "-1",  # Skip NSI matching
            }
            if "Greencross Vets" in properties["name"]:
                properties["brand"] = "Greencross Vets"
                properties["brand_wikidata"] = "Q41179992"
            elif "City Farmers" in properties["name"]:
                properties["brand"] = "City Farmers"
                properties["brand_wikidata"] = "Q117357785"
            else:
                properties["brand"] = "Petbarn"
                properties["brand_wikidata"] = "Q104746468"
            if "Greencross Vets" in location["n"] or "Vet" in location["s"].split(", "):
                apply_category(Categories.VETERINARY, properties)
            if "Pet Hotel" in location["s"].split(", "):
                if "extras" not in properties:
                    properties["extras"] = {}
                if "amenity" in properties["extras"]:
                    properties["extras"]["amenity"] = properties["extras"]["amenity"] + ";animal_boarding"
                else:
                    properties["extras"]["amenity"] = "animal_boarding"
            if "Greencross Vets" not in location["n"]:
                apply_category(Categories.SHOP_PET, properties)
            if "Grooming" in location["s"].split(", "):
                if "extras" not in properties:
                    properties["extras"] = {}
                if "shop" in properties["extras"]:
                    properties["extras"]["shop"] = properties["extras"]["shop"] + ";pet_grooming"
                else:
                    properties["extras"]["shop"] = "pet_grooming"
            properties["opening_hours"] = OpeningHours()
            hours_raw = [s for s in Selector(text=location["oh"]).xpath("//text()").getall() if s.strip()]
            day_names = hours_raw[: len(hours_raw) // 2]
            day_times = hours_raw[len(hours_raw) // 2 :]
            hours_string = ""
            for index, day_name in enumerate(day_names):
                hours_string = f"{hours_string} {day_name}: {day_times[index]}"
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
