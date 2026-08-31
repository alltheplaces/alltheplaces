import json
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class MetaSpider(Spider):
    name = "meta"
    item_attributes = {"brand": "Meta", "brand_wikidata": "Q380"}
    start_urls = ["https://www.metacareers.com/locations"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for region in DictParser.get_nested_key(
            json.loads(response.xpath('//script[contains(text(), "cp_locations_page_regions")]/text()').get()),
            "cp_locations_page_regions",
        ):
            for area in region["areas"]:
                # Within North America the areas are US states, except for Canada
                # Elsewhere the area is the country
                if region["key"] == "North America" and area["name"] != "Canada":
                    state = area["name"]
                    country = "US"
                else:
                    state = None
                    country = area["name"]

                for city in area["cities"]:
                    item = Feature()
                    item["ref"] = item["website"] = "https://www.metacareers.com/{}/".format(city["slug"])
                    item["branch"] = city["display_name"].split(",")[0]
                    place = re.sub(r"\s+Data Center$", "", item["branch"])

                    # Some of the data centres are named after a county e.g. "Crook County Data Center"
                    if not place.endswith(" County"):
                        item["city"] = place
                    item["state"] = state
                    item["country"] = country

                    if city["is_data_center"]:
                        apply_category(Categories.DATA_CENTRE, item)
                    else:
                        apply_category(Categories.OFFICE_IT, item)

                    yield item
