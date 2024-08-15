from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours

OK_FOODS_BRANDS = {
    # "FR SEVENELEVEN": {"brand": "", "brand_wikidata": ""}, # Not sure what this is. Only 1 store at time of writing
    "MEGASAVE": {"brand": "Megasave", "brand_wikidata": "Q116520541", "extras": Categories.SHOP_WHOLESALE.value},
    "OK EXPRESS": {"brand": "OK Express", "brand_wikidata": "Q116520407", "extras": Categories.SHOP_CONVENIENCE.value},
    "OK FOODS": {"brand": "OK Foods", "brand_wikidata": "Q116520377", "extras": Categories.SHOP_SUPERMARKET.value},
    "OK GROCER": {"brand": "OK Grocer", "brand_wikidata": "Q116520377", "extras": Categories.SHOP_SUPERMARKET.value},
    "OK LIQUOR": {"brand": "OK Liquor", "brand_wikidata": "Q116520424", "extras": Categories.SHOP_ALCOHOL.value},
    "OK MINIMARK": {
        "brand": "OK Minimark",
        "brand_wikidata": "Q116520457",
        "extras": Categories.SHOP_CONVENIENCE.value,
    },
    "OK URBAN": {"brand": "OK Urban", "brand_wikidata": "Q116520377", "extras": Categories.SHOP_CONVENIENCE.value},
    "OK VALUE": {"brand": "OK Value", "brand_wikidata": "Q116520377", "extras": Categories.SHOP_CONVENIENCE.value},
    "PRESIDENT HYPER": {
        "brand": "President Hyper",
        "brand_wikidata": "Q116520377",
        "extras": Categories.SHOP_SUPERMARKET.value,
    },
    "SENTRA": {"brand": "Sentra", "brand_wikidata": "Q116520377", "extras": Categories.SHOP_SUPERMARKET.value},
}


class OkFoodsSpider(Spider):
    name = "ok_foods"
    start_urls = [
        "https://www.okfoods.co.za/content/okfoods/za/en_ZA/find-a-store/jcr:content/root/container/okfoodsstorelocator.stores.json?countryId=SouthAfrica",
        "https://www.okfoods.co.za/content/okfoods/na/en_NA/find-a-store/jcr:content/root/container/okfoodsstorelocator.stores.json?countryId=Namibia",
        "https://www.okfoods.co.za/content/okfoods/sz/en_SZ/find-a-store/jcr:content/root/container/okfoodsstorelocator.stores.json?countryId=Eswatini",
    ]
    base_website = {
        "NAMIBIA": "https://www.okfoods.co.za/content/okfoods/na/en_NA/find-a-store.html",
        "ESWATINI": "https://www.okfoods.co.za/content/okfoods/sz/en_SZ/find-a-store.html",
        "SOUTH AFRICA": "https://www.okfoods.co.za/find-a-store.html",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse)

    def parse(self, response):
        for location in response.replace(body=response.json()["results"]).json():
            location["ref"] = location.pop("uid")

            location = {k: v for k, v in location.items() if v != "null"}

            if location.get("phoneInternationalCode") is not None:
                location["phoneNumber"] = (
                    "+" + location["phoneInternationalCode"] + " " + location["phoneNumber"].lstrip("0")
                )

            location["street-address"] = ""
            for i in ["1", "2", "3"]:
                if ("physicalAdd" + i) in location:
                    location["street-address"] += location.pop("physicalAdd" + i) + ", "
            location["street-address"] = location["street-address"].rstrip(", ")

            if "physicalProvince" in location:
                location["province"] = location.pop("physicalProvince")

            item = DictParser.parse(location)

            item["branch"] = location["branch"].replace(location["brand"], "").strip()
            item["website"] = (
                self.base_website[location["country"]]
                + "?stName="
                + location["branch"].replace(" ", "%20")
                + "&storeType="
                + location["brand"].replace(" ", "%20")
            )

            if location["brand"] in OK_FOODS_BRANDS:
                item.update(OK_FOODS_BRANDS[location["brand"]])
                item["name"] = item["brand"]

            try:
                oh = OpeningHours()
                for day in DAYS_FULL:
                    if location[day].strip() != "":
                        oh.add_range(day, location[day].split("-")[0].strip(), location[day].split("-")[1].strip())
                    else:
                        oh.set_closed(day)
                # Fully undefined opening hours should not be treated as closed
                if "".join([location[day].strip() for day in DAYS_FULL]) != "":
                    item["opening_hours"] = oh.as_opening_hours()
            except Exception:
                pass

            yield item
