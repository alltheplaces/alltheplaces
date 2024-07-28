import json
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.tesco_gb import TescoGBSpider
from locations.user_agents import BROWSER_DEFAULT


class TescoEUSpider(scrapy.Spider):
    name = "tesco_eu"
    user_agent = BROWSER_DEFAULT
    COUNTRY_WEBSITE_MAP = {
        "cz": "https://itesco.cz/prodejny/obchody-tesco/",
        "hu": "https://tesco.hu/aruhazak/aruhaz/",
        "sk": "https://tesco.sk/obchody/detail-obchodu/",
    }
    BRANDING_WORDS = ["tesco", "expres", "extra", "expressz"]  # lowercase

    def start_requests(self):
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
            item["website"] = urljoin(self.COUNTRY_WEBSITE_MAP.get(country), f'{store.get("urlname")}/')
            item["opening_hours"] = OpeningHours()
            if timing_text := store.get("opening"):
                for day, hours in json.loads(timing_text).items():
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
