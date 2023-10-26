import scrapy
from geonamescache import GeonamesCache

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class MaxmaraSpider(scrapy.Spider):
    name = "maxmara"
    item_attributes = {"brand": "Max Mara", "brand_wikidata": "Q1151774"}
    gc = GeonamesCache()
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for country_code in self.gc.get_countries().keys():
            url = f"https://world.maxmara.com/store-locator?listJson=true&withoutRadius=false&country={country_code}"
            headers = {
                "authority": "world.maxmara.com",
                "referer": "https://world.maxmara.com/store-locator",
                "user-agent": BROWSER_DEFAULT,
                "x-requested-with": "XMLHttpRequest",
            }
            yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        stores = response.json().get("features")
        for store in stores:
            if not store.get("storeHidden"):
                store_info = store["properties"]
                item = DictParser.parse(store_info)
                item["ref"] = store_info["name"]
                item["name"] = store_info["displayName"]
                item["phone"] = store_info["phone1"]
                item["addr_full"] = store_info["formattedAddress"]

                oh = OpeningHours()
                for day, hours in store_info.get("openingHours").items():
                    for chunk in hours:
                        open_at, close_at = chunk.replace(".", ":").split(" - ")
                        oh.add_range(day=DAYS_EN[day], open_time=open_at, close_time=close_at, time_format="%H:%M")
                item["opening_hours"] = oh

                apply_category(Categories.SHOP_CLOTHES, item)
                apply_category({"clothes": "women"}, item)

                yield item
