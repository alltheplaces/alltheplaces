from typing import Any, Iterable

import chompjs
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.react_server_components import parse_rsc
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class MangoSpider(PlaywrightSpider):
    name = "mango"
    item_attributes = {"brand": "Mango", "brand_wikidata": "Q136503"}
    start_urls = ["https://api.shop.mango.com/cs/online-configuration/v1/country?channelId=shop"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False} | DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for country in response.json()["countries"]:
            if not country.get("hasOnlineAccess"):  # Skip countries with no available stores
                continue
            country_code = country.get("mangoIso")
            default_language = ""
            for language in country.get("languages", []):
                if language.get("defaultLanguage"):
                    default_language = language.get("iso")
                    break
            if default_language:
                yield Request(
                    url=f"https://shop.mango.com/{country_code}/{default_language}/stores".lower(),
                    callback=self.parse_store_details,
                    cb_kwargs={"country": country_code},
                )

    def parse_store_details(self, response: Response, country: str) -> Iterable[Feature]:
        scripts = response.xpath('//script[contains(text(), "addresses")]/text()').getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        if stores_list := DictParser.get_nested_key(dict(parse_rsc(rsc)), "storesFromLite"):
            for store in stores_list:
                store.update(store.pop("addresses", {}))
                item = DictParser.parse(store)
                item["street_address"] = item.pop("addr_full", None)
                item["branch"] = store.get("shoppingCenter")
                item["website"] = "/".join([response.url, store.get("url")])
                item["country"] = country
                apply_category(Categories.SHOP_CLOTHES, item)
                yield item
