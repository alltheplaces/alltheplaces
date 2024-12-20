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
    start_urls = ["https://appapi.littlefreelibrary.org/library/map.json?page_size=500"]
    # It takes a long time for the server to provide 500 locations in a
    # single response. The server rate limits the total number of requests
    # sent in a brief period of time. Thus it's necessary to ask for more
    # locations at a time and wait for the slow responses, and also necessary
    # to add a large delay between requests.
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    download_delay = 60

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_library_list)

    def parse_library_list(self, response):
        for library in response.json()["libraries"]:
            properties = {
                "ref": library.get("Official_Charter_Number__c"),
                "lat": library.get("Library_Geolocation__Latitude__s"),
                "lon": library.get("Library_Geolocation__Longitude__s"),
                "street_address": library.get("Street__c"),
                "city": library.get("City__c"),
                "state": library.get("State_Province_Region__c"),
                "postcode": library.get("Postal_Zip_Code__c"),
                "country": library.get("Country__c"),
                "image": library.get("primary_image"),
                # These fields could potentially be considered
                # personal/private information and don't add much value
                # to ATP. It's easier to ignore these fields.
                # "operator": library.get("Primary_Steward_s_Name__c"),
                # "phone": library.get("Primary_Steward_s_Phone__c"),
                # "email": library.get("Primary_Steward_s_Email__c"),
            }
            if library.get("Library_Name__c"):
                properties["name"] = library.get("Library_Name__c")
            elif library.get("List_As_Name__c"):
                properties["name"] = library.get("List_As_Name__c")
            else:
                properties["name"] = library.get("Name")
            yield Feature(**properties)

        if "&page=" not in response.url:
            for page in range(2, response.json()["page_count"]):
                yield JsonRequest(response.url + f"&page={page}", callback=self.parse_library_list)
