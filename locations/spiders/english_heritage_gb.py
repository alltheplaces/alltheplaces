from locations.categories import Extras, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class EnglishHeritageGBSpider(JSONBlobSpider):
    name = "english_heritage_gb"
    item_attributes = {"brand": "English Heritage", "brand_wikidata": "Q936287", "nsi_id": "N/A"}
    start_urls = ["https://www.english-heritage.org.uk/api/PropertySearch/GetAll"]
    no_refs = True
    locations_key = "Results"
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, location):
        item["website"] = response.urljoin(location["Path"])

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
        if location["PrimaryPropertyType"] == 2:
            item["extras"]["historic"] = "castle"
        if location["PrimaryPropertyType"] == 3:
            item["extras"]["leisure"] = "garden"
        if location["PrimaryPropertyType"] == 4:
            item["extras"]["historic"] = "building"
        if location["PrimaryPropertyType"] == 5:
            item["extras"]["historic"] = "building"
        if location["PrimaryPropertyType"] == 6:
            item["extras"]["historic"] = "archaeological_site"
            item["extras"]["historic:civilization"] = "prehistoric"
        if location["PrimaryPropertyType"] == 7:
            item["extras"]["historic"] = "archaeological_site"
            item["extras"]["historic:civilization"] = "roman"

        yield item
