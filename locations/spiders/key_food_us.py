from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class KeyFoodUSSpider(Spider):
    name = "key_food_us"
    allowed_domains = ["keyfoodstores.keyfood.com"]
    start_urls = ["https://keyfoodstores.keyfood.com/store/keyFood/en/store-locator?q=90210&page=0&radius=100000&all=true"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

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
            item["street_address"] = ", ".join(filter(None, [location["line1"], location["line2"]]))
            item["website"] = location["siteUrl"] + location["url"].split("?", 1)[0]

            if "www.keyfood.com" in item["website"] or "keyfoodstores.keyfood.com" in item["website"]:
                item["brand"] = "Key Food"
                item["brand_wikidata"] = "Q6398037"
            elif "keyfoodmarketplace.keyfood.com" in item["website"]:
                item["brand"] = "Key Food Marketplace"
                #item["brand_wikidata"] = ""
            elif "urbanmarketplace.keyfood.com" in item["website"]:
                item["brand"] = "Key Food Urban Marketplace"
                #item["brand_wikidata"] = ""
            elif "superfresh.keyfood.com" in item["website"]:
                item["brand"] = "SuperFresh"
                #item["brand_wikidata"] = ""
            elif "galafoods.keyfood.com" in item["website"]:
                item["brand"] = "Gala Foods"
                #item["brand_wikidata"] = ""
            elif "galafresh.keyfood.com" in item["website"]:
                item["brand"] = "GalaFresh Farms"
                #item["brand_wikidata"] = ""
            elif "fooduniverse.keyfood.com" in item["website"]:
                item["brand"] = "Food Universe"
                #item["brand_wikidata"] = ""
            elif "foodemporium.keyfood.com" in item["website"]:
                item["brand"] = "The Food Emporium"
                #item["brand_wikidata"] = ""
            elif "fooddynasty.keyfood.com" in item["website"]:
                item["brand"] = "Food Dynasty"
                #item["brand_wikidata"] = ""
            elif "tropicalsupermarket.keyfood.com" in item["website"]:
                item["brand"] = "Tropical Supermarket"
                #item["brand_wikidata"] = ""
            elif "halseytradersmarket.keyfood.com" in item["website"]:
                item["brand"] = "Halsey Traders Market"
                #item["brand_wikidata"] = ""
            elif "marketplace.keyfood.com" in item["website"]:
                item["brand"] = "Marketplace"
                #item["brand_wikidata"] = ""
            elif "ernestklein.keyfood.com" in item["website"]:
                item["brand"] = "Ernest Klein"
                #item["brand_wikidata"] = ""

            apply_category(Categories.SHOP_SUPERMARKET, item)

            item["opening_hours"] = OpeningHours()
            if location.get("open24Hours"):
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            else:
                for day_name, day_hours in location["openings"].items():
                    item["opening_hours"].add_range(day_name, day_hours.split(" - ", 1)[0], day_hours.split(" - ", 1)[1], "%I:%M %p")

            yield item

        next_page = response.meta["page"] + 1
        if next_page * 250 < response.json()["total"]:
            yield JsonRequest(url=self.start_urls[0].replace("&page=0", "&page=" + str(next_page)), meta={"page": next_page})
