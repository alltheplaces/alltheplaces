from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class FantasticFurnitureAUSpider(Spider):
    name = "fantastic_furniture_au"
    item_attributes = {"brand": "Fantastic Furniture", "brand_wikidata": "Q18164803"}
    allowed_domains = ["api.fantasticfurniture.com.au"]
    start_urls = ["https://api.fantasticfurniture.com.au/occ/v2/fantasticfurniture-spa/store-finder?fields=FULL&page=0"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, meta={"page": 0})

    def parse(self, response):
        for location in response.json()["searchPageData"]["stores"]:
            if location["type"] != "STORE":
                continue

            item = DictParser.parse(location)
            item["ref"] = location["code"]
            item["street_address"] = clean_address([location["address"].get("line1"), location["address"].get("line2")])
            item["addr_full"] = location["address"]["formattedAddress"].replace(" , ", ", ")
            item.pop("street")
            item["state"] = location["address"]["region"]["name"]
            item["phone"] = location["address"].get("phone")
            item.pop("website")
            for image in location["storeImages"]:
                if image["format"] == "storeDetail":
                    item["image"] = "https://api.fantasticfurniture.com.au" + image["url"]
                    break

            item["opening_hours"] = OpeningHours()
            for day_hours in location["openingHours"]["weekDayOpeningList"]:
                if day_hours["closed"]:
                    continue
                item["opening_hours"].add_range(
                    day_hours["weekDay"],
                    day_hours["openingTime"]["formattedHour"],
                    day_hours["closingTime"]["formattedHour"],
                    "%I:%M %p",
                )

            yield item

        if response.meta["page"] == 0:
            if response.json()["searchPageData"]["pagination"]["totalPages"] == 1:
                return
            for page in range(1, response.json()["searchPageData"]["pagination"]["totalPages"] - 1, 1):
                yield JsonRequest(url=response.url.replace("&page=0", f"&page={page}"), meta={"page": page})
