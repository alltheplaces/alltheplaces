from urllib.parse import urljoin

from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class EnglishHeritageGBSpider(JSONBlobSpider):
    name = "english_heritage_gb"
    item_attributes = {"brand": "English Heritage", "brand_wikidata": "Q936287"}
    start_urls = ["https://www.english-heritage.org.uk/api/PropertySearch/GetAll"]
    no_refs = True
    locations_key = "Results"
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "user-agent": BROWSER_DEFAULT,
        },
    }

    # FACILITIES location["SelectedFacilityList"]
    # 172 cafe/restaurant
    # 173 dog friendly
    # 174 family favourites
    # 175 picnic seating
    # 176 play area
    # 177 Wheelchair access

    # CATEGORIES location["PrimaryPropertyType"]
    # building:church 1 Abbeys and churches
    # building:castle 2 Castles and Forts
    # leisure:garden 3 Gardens
    # building:yes,historic:castle 4 Houses and Palaces
    # historic:building,building:yes 5 Medieval and Tudor
    # historic=archaeological_site, historic:civilization=prehistoric  6 Prehistoric
    # historic=archaeological_site, historic:civilization=roman 7 Roman

    def post_process_item(self, item, response, location):
        item["website"] = urljoin("https://www.english-heritage.org.uk", location["Path"])
        # apply_category(Categories.TOURISM_ATTRACTION, item)

        # if location["PrimaryPropertyType"] == 1:
        #    apply_category(Categories.CHURCH, item)

        yield item
