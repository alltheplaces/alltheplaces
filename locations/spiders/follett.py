from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import clean_facebook, clean_twitter


class FollettSpider(Spider):
    name = "follett"
    item_attributes = {"operator": "Follett Corporation", "operator_wikidata": "Q5464641"}
    allowed_domains = ["svc.bkstr.com"]
    start_urls = ["https://svc.bkstr.com/store/byName?storeType=FMS&langId=-1&schoolName=*"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_location_list)

    def parse_location_list(self, response):
        for location in response.json()["storeResultList"]:
            if not location["storeStatus"]:
                continue
            if "store/home" in location["storeUrl"]:
                store_name = location["storeUrl"].replace("/home", "")
            elif "content.efollett.com/canada/" in location["storeUrl"]:
                store_name = location["storeUrl"].split("/canada/", 1)[1].split(".html", 1)[0] + "store"
            yield JsonRequest(url=f"https://svc.bkstr.com/store/config?storeName={store_name}")

    def parse(self, response):
        location = response.json()
        if location["state"] != "open":
            return

        properties = {
            "ref": location["storeId"],
            "phone": location["storeExtensionData"][0].get("phone1"),
            "twitter": clean_twitter(location["storeExtensionData"][0].get("twitterUrl", "")),
            "facebook": clean_facebook(location["storeExtensionData"][0].get("facebookUrl", "")),
            "website": "https://www.bkstr.com/" + response.url.split("storeName=", 1)[1] + "/home",
        }

        for name_data in location["description"]:
            if name_data["languageId"] == "-1":  # English
                properties["name"] = name_data["displayName"]
                break

        for location_data in location["locationInfo"]:
            if location_data["languageId"] == "-1":  # English
                properties["street_address"] = clean_address(location_data["address"]["addressLine"])
                properties["city"] = location_data["address"].get("city")
                properties["state"] = location_data["address"].get("stateOrProvinceName")
                properties["country"] = location_data["address"].get("country")
                properties["postcode"] = location_data["address"].get("zipOrPostalCode")
                break

        for contact_data in location["contactInfo"]:
            if contact_data["languageId"] == "-1":  # English
                properties["email"] = location_data["address"].get("emailAddress1")
                break

        for store_hours in location["storeHours"]["storeHours"]:
            if store_hours["sequence"] == 0:  # Usual bookshop hours
                hours_string = ""
                for day_name in DAYS_FULL:
                    if not store_hours.get(day_name.lower()):
                        continue
                    if "/" in store_hours[day_name.lower()]:
                        day_hours = store_hours[day_name.lower()].split("/", 1)[1]
                    else:
                        day_hours = store_hours[day_name.lower()]
                    hours_string = f"{hours_string} {day_name}: {day_hours}"
                properties["opening_hours"] = OpeningHours()
                properties["opening_hours"].add_ranges_from_string(hours_string)

        apply_category(Categories.SHOP_BOOKS, properties)
        properties["extras"]["books"] = "academic"

        yield Feature(**properties)
