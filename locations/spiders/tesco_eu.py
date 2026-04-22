from json import loads
from typing import AsyncIterator
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.tesco_gb import TescoGBSpider
from locations.user_agents import BROWSER_DEFAULT


# TODO: modernize spider to use https://www.tesco.sk/obchody/directory pages + structured data
class TescoEUSpider(Spider):
    name = "tesco_eu"
    COUNTRY_WEBSITE_MAP = {
        "cz": "https://www.itesco.cz/prodejny/",
        "hu": "https://www.tesco.hu/aruhazak/",
        "sk": "https://www.tesco.sk/obchody/",
    }
    BRANDING_WORDS = ["tesco", "expres", "extra", "expressz"]  # lowercase
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[Request]:
        for country, website in self.COUNTRY_WEBSITE_MAP.items():
            yield Request(
                url=f"https://{urlparse(website).hostname}/Ajax?type=fetch-stores-for-area&bounds[nw][lat]=90&bounds[nw][lng]=-180&bounds[ne][lat]=90&bounds[ne][lng]=180&bounds[sw][lat]=-90&bounds[sw][lng]=-180&bounds[se][lat]=-90&bounds[se][lng]=180",
                cb_kwargs=dict(country=country),
            )

    def parse(self, response, country):
        for store in response.json()["stores"]:
            store["street-address"] = store.pop("address", "")
            item = DictParser.parse(store)
            if name := item.pop("name"):
                item["branch"] = " ".join([word for word in name.split(" ") if word.lower() not in self.BRANDING_WORDS])
            item["ref"] = store["goldid"]
            item["lat"] = store.get("gpslat")
            item["lon"] = store.get("gpslng")
            item["country"] = country
            item["opening_hours"] = OpeningHours()
            item["website"] = self.COUNTRY_WEBSITE_MAP.get(
                country
            )  # There is 'urlname' attribute, but it's not leading to the store page
            if timing_text := store.get("opening"):
                for day, hours in loads(timing_text).items():
                    open_time, close_time = hours if hours else [None, None]
                    item["opening_hours"].add_range(DAYS[int(day) - 1], open_time, close_time)

            # typeid is not consistent across countries, also sometimes not reliable to determine a brand
            store_names = [name.title() for name in [store.get("name", ""), store.get("webname", "")]]
            if any("Extra" in name for name in store_names):
                apply_category(Categories.SHOP_SUPERMARKET, item)
                item.update(TescoGBSpider.TESCO_EXTRA)
            elif any("Expres" in name for name in store_names):
                apply_category(Categories.SHOP_CONVENIENCE, item)
                item.update(TescoGBSpider.TESCO_EXPRESS)
            else:
                apply_category(Categories.SHOP_SUPERMARKET, item)
                item.update(TescoGBSpider.TESCO)
            yield item
