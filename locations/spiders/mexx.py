from typing import AsyncIterator

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class MexxSpider(Spider):
    name = "mexx"
    item_attributes = {"brand": "Mexx", "brand_wikidata": "Q1837290"}
    gc = GeonamesCache()
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "authority": "www.mexx.com",
            "referer": "https://www.mexx.com/en/storepickup",
            "user-agent": BROWSER_DEFAULT,
        },
    }

    async def start(self) -> AsyncIterator[Request]:
        for country_code in self.gc.get_countries().keys():
            url = f"https://www.mexx.com/en/storepickup/index/loadstore/?tagIds%5B%5D=3&countryId={country_code}"
            yield Request(url=url, meta={"country_code": country_code}, callback=self.parse)

    def parse(self, response):
        stores = response.json().get("storesjson")
        for store in stores:
            store["country_code"] = response.meta["country_code"]
            yield Request(
                f"https://www.mexx.com/en/{store['rewrite_request_path']}", meta=store, callback=self.parse_store
            )

    def parse_store(self, response):
        store = response.meta
        item = DictParser.parse(store)
        item["ref"] = store["storepickup_id"]
        item["email"] = response.xpath("//a[@class='group-info' and contains(@href, 'mailto')]/text()").get()

        oh = OpeningHours()
        open_hours = response.xpath("//tr[td[@class='time-label']]/td[string-length(text()) > 0]/text()").getall()
        for day, hours in zip(open_hours[::2], open_hours[1::2]):
            day = day.replace(":", "")
            if hours != "closed":
                open_at, close_at = hours.split(" - ")
                oh.add_range(day=DAYS_EN[day], open_time=open_at, close_time=close_at, time_format="%H:%M")
        item["opening_hours"] = oh

        yield item
