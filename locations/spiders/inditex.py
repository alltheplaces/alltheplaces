from collections import Counter
from typing import Any, Iterable

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class InditexSpider(PlaywrightSpider):
    name = "inditex"
    my_brands = {
        "bershka": {"brand": "Bershka", "brand_wikidata": "Q827258"},
        "massimodutti": {"brand": "Massimo Dutti", "brand_wikidata": "Q788231"},
        "oysho": {"brand": "Oysho", "brand_wikidata": "Q3327046"},
        "zarahome": {"brand": "Zara Home", "brand_wikidata": "Q3114054"},
        "stradivarius": {"brand": "Stradivarius", "brand_wikidata": "Q3322945"},
        "pullandbear": {"brand": "Pull & Bear", "brand_wikidata": "Q691029"},
        "lefties": {"brand": "Lefties", "brand_wikidata": "Q12391713"},
    }
    # Each site has the same multi-brand catalogue JSON, could have picked any site!
    start_urls = ["https://www.massimodutti.com/itxrest/2/web/seo/config?appId=1"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000,
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 5,
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        config = response.json()["seoParamMap"]
        for store_id, country in config["storeId"].items():
            for brand in config["brandId"].values():
                if brand == "dutti":
                    brand = "massimodutti"
                if brand == "uterque":
                    # Discontinued brand, still in their config as time of writing.
                    continue
                if brand == "zara":
                    # Has its own spider, and zara.com blocks this crawler.
                    continue
                url = "https://www.{}.com/itxrest/2/bam/store/{}/physical-stores-by-country?countryCode={}".format(
                    brand,
                    store_id,
                    country.upper(),
                )
                yield scrapy.http.JsonRequest(url, callback=self.parse_stores, cb_kwargs=dict(brand=brand))

    def parse_stores(self, response: Response, brand: str) -> Iterable[Feature]:
        stores = response.json()["stores"]
        # Central customer-service numbers are shared by many stores of a brand in a country
        phone_counts = Counter((store.get("phones") or [None])[0] for store in stores)
        for store in stores:
            item = DictParser.parse(store)
            if brand == "bershka":
                # Bershka's per-store URLs 404, only a generic landing page exists.
                item["website"] = None
            else:
                item["website"] = "https://www.{}.com/".format(brand) + item["country"].lower()
            item.update(self.my_brands.get(brand))
            phone = (store.get("phones") or [None])[0]
            item["phone"] = phone if phone_counts[phone] == 1 else None
            item["branch"] = item.pop("name")
            item["street_address"] = store["addressLines"][0]
            day_strips = {}
            for record in store["openingHours"]["schedule"]:
                for day in record["weekdays"]:
                    day_strips[day] = record["timeStripList"]
            oh = OpeningHours()
            for day, time_strips in day_strips.items():
                for time_strip in time_strips:
                    oh.add_range(DAYS[day - 1], time_strip["initHour"], time_strip["endHour"])
            item["opening_hours"] = oh
            yield item
