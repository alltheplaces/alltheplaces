from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class GreencrossAUSpider(Spider):
    name = "greencross_au"
    allowed_domains = ["www.petbarn.com.au"]
    start_urls = ["https://www.petbarn.com.au/store-finder/index/dataAjax/?types=pb%2Cgx%2Ccf"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
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
                "website": response.urljoin(location["u"]),
            }
            if "Greencross Vets" in properties["name"]:
                properties["brand"] = "Greencross Vets"
                properties["brand_wikidata"] = "Q41179992"
                properties["branch"] = properties.pop("name").removeprefix("Greencross Vets ")
            elif "City Farmers" in properties["name"]:
                properties["brand"] = "City Farmers"
                properties["brand_wikidata"] = "Q117357785"
                properties["branch"] = properties.pop("name").removeprefix("City Farmers ")
            else:
                properties["brand"] = "Petbarn"
                properties["brand_wikidata"] = "Q104746468"
                properties["branch"] = properties.pop("name")

            properties["opening_hours"] = OpeningHours()
            hours_raw = [s for s in Selector(text=location["oh"]).xpath("//text()").getall() if s.strip()]
            day_names = hours_raw[: len(hours_raw) // 2]
            day_times = hours_raw[len(hours_raw) // 2 :]
            hours_string = ""
            for index, day_name in enumerate(day_names):
                hours_string = f"{hours_string} {day_name}: {day_times[index]}"
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
