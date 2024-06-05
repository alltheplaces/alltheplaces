import reverse_geocoder
from scrapy import Request, Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class HouseAUSpider(Spider):
    name = "house_au"
    allowed_domains = ["www.house.com.au"]
    start_urls = ["https://www.house.com.au/api/get-stores"]
    brands = {
        "House Bed & Bath": {
            "brand": "House Bed & Bath",
            "brand_wikidata": "",
            "extras": Categories.SHOP_HOUSEHOLD_LINEN.value,
        },
        "House": {"brand": "House", "brand_wikidata": "Q117921987", "extras": Categories.SHOP_HOUSEWARE.value},
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, method="POST")

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)

            for brand_name in self.brands.keys():
                if item["name"].startswith(f"{brand_name} "):
                    item.update(self.brands[brand_name])
                    item["branch"] = item["name"].replace(f"{brand_name} ", "")
                    break

            # Some stores have wildly incorrect coordinates for
            # locations as far away as France. Only add geometry
            # where coordinates existing within Australia.
            if result := reverse_geocoder.get((location["latitude"], location["longitude"]), mode=1, verbose=False):
                if result["cc"] == "AU":
                    item["geometry"] = location["location"]

            item["street_address"] = clean_address([location["address1"], location["address2"]])
            item["website"] = "https://www.house.com.au/stores/" + location["slug"]

            item["opening_hours"] = OpeningHours()
            for day_name, hours in location["storeHours"].items():
                if hours["open"] == "-" or hours["close"] == "-" or hours["close"] == "17:3016:00":
                    continue
                item["opening_hours"].add_range(
                    day_name.title(),
                    hours["open"].replace(".", ":"),
                    hours["close"].replace(".", ":").replace(":-", ":"),
                )

            yield item
