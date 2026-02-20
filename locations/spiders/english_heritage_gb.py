from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EnglishHeritageGBSpider(JSONBlobSpider):
    name = "english_heritage_gb"
    item_attributes = {"operator": "English Heritage", "operator_wikidata": "Q936287", "nsi_id": "N/A"}
    start_urls = ["https://www.english-heritage.org.uk/api/PropertySearch/GetAll"]
    locations_key = "Results"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept": "application/json"}}

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["website"] = response.urljoin(location["Path"])
        item["image"] = response.urljoin(location["ImagePath"])

        apply_category({"tourism": "attraction"}, item)

        # FACILITIES location["SelectedFacilityList"]
        # 172 cafe/restaurant
        # 173 dog friendly
        # 174 family favourites
        # 175 picnic seating
        # 176 play area
        # 177 Wheelchair access

        apply_yes_no("food", item, 172 in location["SelectedFacilityList"])
        apply_yes_no(Extras.PETS_ALLOWED, item, 173 in location["SelectedFacilityList"])
        apply_yes_no(Extras.WHEELCHAIR, item, 177 in location["SelectedFacilityList"])

        # CATEGORIES location["PrimaryPropertyType"]
        # building:church 1 Abbeys and churches
        # building:castle 2 Castles and Forts
        # leisure:garden 3 Gardens
        # building:yes,historic:castle 4 Houses and Palaces
        # historic:building,building:yes 5 Medieval and Tudor
        # historic=archaeological_site, historic:civilization=prehistoric  6 Prehistoric
        # historic=archaeological_site, historic:civilization=roman 7 Roman

        if location["PrimaryPropertyType"] == 1:
            item["extras"]["historic"] = "church"
        elif location["PrimaryPropertyType"] == 2:
            item["extras"]["historic"] = "castle"
        elif location["PrimaryPropertyType"] == 3:
            item["extras"]["leisure"] = "garden"
        elif location["PrimaryPropertyType"] == 4:
            item["extras"]["historic"] = "building"
        elif location["PrimaryPropertyType"] == 5:
            item["extras"]["historic"] = "building"
        elif location["PrimaryPropertyType"] == 6:
            item["extras"]["historic"] = "archaeological_site"
            item["extras"]["historic:civilization"] = "prehistoric"
        elif location["PrimaryPropertyType"] == 7:
            item["extras"]["historic"] = "archaeological_site"
            item["extras"]["historic:civilization"] = "roman"

        yield item
