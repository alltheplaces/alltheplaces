from typing import Any, AsyncIterator

import chompjs
from scrapy import Request
from scrapy.http import JsonRequest, Response, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class HornbachSpider(PlaywrightSpider):
    name = "hornbach"
    BRANDS = {
        "bodenhaus": {"name": "Bodenhaus", "brand": "Bodenhaus"},
        "hornbach": {"brand": "HORNBACH", "brand_wikidata": "Q685926"},
    }
    COUNTRY_MAP = [
        # url, locale, company code
        ("https://www.bodenhaus.de", "de_DE", "1060"),
        ("https://www.hornbach.de", "de_DE", "1001"),
        ("https://www.hornbach.at", "de_AT", "1124"),
        ("https://www.hornbach.ch", "de_CH", "1043"),
        ("https://www.hornbach.lu", "fr_LU", "1038"),
        ("https://www.hornbach.cz", "cs_CZ", "1120"),
        ("https://www.hornbach.nl", "nl_NL", "1042"),
        ("https://www.hornbach.ro", "ro_RO", "1130"),
        ("https://www.hornbach.se", "sv_SE", "1442"),
        ("https://www.hornbach.sk", "sk_SK", "1123"),
    ]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    requires_proxy = True  # Helps to skip anti bot protection

    async def start(self) -> AsyncIterator[Request]:
        for url, locale, company_code in self.COUNTRY_MAP:
            yield Request(url=url, cb_kwargs=dict(locale=locale, company_code=company_code))

    def parse(self, response: Response, locale: str, company_code: str) -> Any:
        # Anti-bot protection may return a page without the required data.
        # Try to fetch updated API config values; if it fails, fall back to the default values.
        try:
            client_config = chompjs.parse_js_object(
                response.xpath('//script[contains(text(), "companyCode")]/text()').get()
            )
            locale = client_config["locale"]
            company_code = client_config["companyCode"]
        except Exception:
            self.logger.warning(f"Failed to fetch updated API config values; using default values for: {response.url}")

        yield JsonRequest(
            url=f"https://svc.hornbach.de/cmscontent-service/stores?language={locale.replace('-', '_')}&companyCode={company_code}",
            callback=self.parse_locations,
        )

    def parse_locations(self, response: TextResponse) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["branch"] = item.pop("name", "").removeprefix("BODENHAUS ").removeprefix("HORNBACH ").strip()

            if brand_info := self.BRANDS.get(store.get("client")):
                item.update(brand_info)
            if store.get("client") == "bodenhaus":
                apply_category(Categories.SHOP_FLOORING, item)

            item["opening_hours"] = self.parse_opening_hours(store.get("simplifiedOpeningHours", []))
            yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            start_day = rule.get("weekdayFrom")
            end_day = rule.get("weekdayTo") or start_day
            if start_day and end_day:
                oh.add_days_range(day_range(start_day, end_day), rule["timeFrom"], rule["timeTo"], "%H:%M:%S")
        return oh
