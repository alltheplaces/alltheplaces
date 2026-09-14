import json
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class TractorSupplySpider(SitemapSpider):
    name = "tractor_supply"
    item_attributes = {"brand": "Tractor Supply Company", "brand_wikidata": "Q15109925"}
    sitemap_urls = ["https://www.tractorsupply.com/sitemap_stores.xml"]
    sitemap_rules = [(r"/tsc/store_.+_(\d+)$", "parse")]
    requires_proxy = "US"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        ref = response.url.rsplit("_", 1)[-1]
        for query in data["props"]["pageProps"]["dehydratedState"]["queries"]:
            for entry in ((query.get("state") or {}).get("data") or {}).get("StoreList", []):
                store = entry["value"]
                if store.get("storenum") != ref:
                    continue
                store["street_address"] = ", ".join(
                    filter(None, [store.get("address1"), store.get("address2"), store.get("address3")])
                )
                store["postcode"] = store.get("zipcode")
                store["phone"] = store.get("phone1")
                item = DictParser.parse(store)
                item["ref"] = store["storenum"]
                item["branch"] = store.get("store_name")
                item["name"] = None
                item["website"] = response.url
                item["opening_hours"] = self.parse_hours(store.get("operating_hours"))
                yield item
                return

    def parse_hours(self, raw: str | None) -> OpeningHours:
        oh = OpeningHours()
        for day, value in json.loads(raw or "{}").items():
            if " - " in value:
                open_time, close_time = value.split(" - ")
                oh.add_range(day, open_time.strip(), close_time.strip(), time_format="%I:%M %p")
            elif "close" in value.lower():
                oh.set_closed(day)
        return oh
