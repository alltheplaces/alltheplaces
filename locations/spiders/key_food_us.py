from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class KeyFoodUSSpider(Spider):
    name = "key_food_us"
    allowed_domains = ["keyfoodstores.keyfood.com"]
    start_urls = [
        "https://keyfoodstores.keyfood.com/store/keyFood/en/store-locator?q=90210&page=0&radius=100000&all=true"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    brands = {
        "https://ernestklein.keyfood.com/store": {"brand": "Ernest Klein"},
        "https://fooddynasty.keyfood.com/store": {"brand": "Food Dynasty"},
        "https://foodemporium.keyfood.com/store": {"brand": "The Food Emporium"},
        "https://fooduniverse.keyfood.com/store": {"brand": "Food Universe"},
        "https://galafoods.keyfood.com/store": {"brand": "Gala Foods"},
        "https://galafresh.keyfood.com/store": {"brand": "GalaFresh Farms"},
        "https://halseytradersmarket.keyfood.com/store": {"brand": "Halsey Traders Market"},
        "https://keyfoodmarketplace.keyfood.com/store": {"brand": "Key Food Marketplace"},
        "https://keyfoodstores.keyfood.com/store": {"brand": "Key Food", "brand_wikidata": "Q6398037"},
        "https://marketplace.keyfood.com/store": {"brand": "Marketplace"},
        "https://superfresh.keyfood.com/store": {"brand": "SuperFresh"},
        "https://tropicalsupermarket.keyfood.com/store": {"brand": "Tropical Supermarket"},
        "https://urbanmarketplace.keyfood.com/store": {"brand": "Key Food Urban Marketplace"},
        "https://www.keyfood.com/store": {"brand": "Key Food", "brand_wikidata": "Q6398037"},
    }

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, meta={"page": 0})

    def parse(self, response):
        for location in response.json()["data"]:
            if location.get("comingSoon") != "false":
                continue

            item = DictParser.parse(location)
            item["ref"] = location["name"]
            item["name"] = location["displayName"]
            item["street_address"] = clean_address([location["line1"], location["line2"]])
            item["website"] = location["siteUrl"] + location["url"].split("?", 1)[0]

            if brand := self.brands.get(location["siteUrl"]):
                item.update(brand)

            apply_category(Categories.SHOP_SUPERMARKET, item)

            item["opening_hours"] = OpeningHours()
            if location.get("open24Hours"):
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            else:
                for day_name, day_hours in location["openings"].items():
                    item["opening_hours"].add_range(day_name, *day_hours.split(" - ", 1), "%I:%M %p")

            yield item

        next_page = response.meta["page"] + 1
        if next_page * 250 < response.json()["total"]:
            yield JsonRequest(
                url=self.start_urls[0].replace("&page=0", "&page=" + str(next_page)), meta={"page": next_page}
            )
