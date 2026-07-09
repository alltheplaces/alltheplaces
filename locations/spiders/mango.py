import json
from typing import Any, Iterable

import chompjs
from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor

from locations.dict_parser import DictParser
from locations.hours import (
    DAYS_AR,
    DAYS_BG,
    DAYS_CN,
    DAYS_CZ,
    DAYS_DE,
    DAYS_EN,
    DAYS_ES,
    DAYS_FR,
    DAYS_GR,
    DAYS_HR,
    DAYS_HU,
    DAYS_ID,
    DAYS_IT,
    DAYS_KR,
    DAYS_NL,
    DAYS_NO,
    DAYS_PL,
    DAYS_PT,
    DAYS_RO,
    DAYS_RU,
    DAYS_SE,
    DAYS_TH,
    DAYS_TR,
    DAYS_UA,
    OpeningHours,
    sanitise_day,
)
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.react_server_components import parse_rsc
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class MangoSpider(PlaywrightSpider):
    name = "mango"
    item_attributes = {"brand": "Mango", "brand_wikidata": "Q136503"}
    start_urls = ["https://api.shop.mango.com/cs/online-configuration/v1/country?channelId=shop"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS

    LANGUAGE_DAYS_MAP = {
        "AR": DAYS_AR,
        "BG": DAYS_BG,
        "CS": DAYS_CZ,
        "DE": DAYS_DE,
        "EL": DAYS_GR,
        "ES": DAYS_ES,
        "FR": DAYS_FR,
        "HR": DAYS_HR,
        "HU": DAYS_HU,
        "ID": DAYS_ID,
        "IT": DAYS_IT,
        "KO": DAYS_KR,
        "NO": DAYS_NO,
        "NL": DAYS_NL,
        "PT": DAYS_PT,
        "PL": DAYS_PL,
        "RO": DAYS_RO,
        "RU": DAYS_RU,
        "SV": DAYS_SE,
        "TH": DAYS_TH,
        "TR": DAYS_TR,
        "UK": DAYS_UA,
        "ZH": DAYS_CN,
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for country in json.loads(response.xpath("//pre/text()").get())["countries"]:
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
                    callback=self.parse_store_urls,
                    cb_kwargs={"country": country_code, "language": default_language.upper()},
                )

    def parse_store_urls(self, response: Response, country: str, language: str) -> Any:
        for link in LinkExtractor(allow=r"/[a-z]{2}/[a-z]{2}/stores/[^/]+/[^/]+/\d+$").extract_links(response):
            yield response.follow(
                url=link.url, callback=self.parse_store_details, cb_kwargs={"country": country, "language": language}
            )

    def parse_store_details(self, response: Response, country: str, language: str) -> Iterable[Feature]:
        scripts = response.xpath('//script[contains(text(), "timeSchedule")]/text()').getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        if store_data := DictParser.get_nested_key(dict(parse_rsc(rsc)), "stores"):
            store = store_data[0]
            store.update(store.pop("details", {}))
            store.update(store.pop("addresses", {}))
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full", None)
            item["branch"] = store.get("shoppingCenter")
            item["website"] = response.url
            item["country"] = country
            try:
                item["opening_hours"] = self.parse_opening_hours(store.get("timeSchedule", []), language)
            except Exception as e:
                self.logger.error(f'Failed to parse opening hours:{store.get("timeSchedule")} {e}')
            yield item

    def parse_opening_hours(self, rules: list[dict], language: str) -> OpeningHours:
        opening_hours = OpeningHours()
        days = self.LANGUAGE_DAYS_MAP.get(language) or DAYS_EN
        for day_time in rules:
            if day := sanitise_day(day_time.get("dayOfWeek"), days):
                for open_close_time in day_time.get("timeList") or []:
                    open_time = open_close_time.get("openHour")
                    close_time = open_close_time.get("closeHour")
                    if open_time != "-":
                        opening_hours.add_range(day=day, open_time=open_time, close_time=close_time)
        return opening_hours
