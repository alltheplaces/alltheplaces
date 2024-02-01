from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.items import Feature


class LittleFreeLibrarySpider(Spider):
    name = "little_free_library"
    item_attributes = {
        "brand": "Little Free Library",
        "brand_wikidata": "Q6650101",
        "extras": Categories.PUBLIC_BOOKCASE.value,
    }
    allowed_domains = ["appapi.littlefreelibrary.org"]
    start_urls = ["https://appapi.littlefreelibrary.org/library/pin.json?page_size=500&distance=15000&near=0,0"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_library_list)

    def parse_library_list(self, response):
        for library in response.json()["libraries"]:
            library_id = library["id"]
            yield JsonRequest(
                url=f"https://appapi.littlefreelibrary.org/libraries/{library_id}.json", callback=self.parse_library
            )
        if "&page=" not in response.url:
            for page in range(2, response.json()["page_count"]):
                yield JsonRequest(response.url + f"&page={page}", callback=self.parse_library_list)

    def parse_library(self, response):
        location = response.json()
        properties = {
            "ref": location.get("Official_Charter_Number__c"),
            "lat": location.get("Library_Geolocation__Latitude__s"),
            "lon": location.get("Library_Geolocation__Longitude__s"),
            "street_address": location.get("Street__c"),
            "city": location.get("City__c"),
            "state": location.get("State_Province_Region__c"),
            "postcode": location.get("Postal_Zip_Code__c"),
            "country": location.get("Country__c"),
            "image": location.get("primary_image"),
            # These fields could potentially be considered
            # personal/private information and don't add much value
            # to ATP. It's easier to ignore these fields.
            # "operator": location.get("Primary_Steward_s_Name__c"),
            # "phone": location.get("Primary_Steward_s_Phone__c"),
            # "email": location.get("Primary_Steward_s_Email__c"),
        }
        if location.get("Library_Name__c"):
            properties["name"] = location.get("Library_Name__c")
        elif location.get("List_As_Name__c"):
            properties["name"] = location.get("List_As_Name__c")
        else:
            properties["name"] = location.get("Name")
        yield Feature(**properties)
