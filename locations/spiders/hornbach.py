from typing import Any

import chompjs
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
    start_urls = [
        "https://www.bodenhaus.de",
        "https://www.hornbach.de",
        "https://www.hornbach.at",
        "https://www.hornbach.ch",
        "https://www.hornbach.lu",
        "https://www.hornbach.cz",
        "https://www.hornbach.nl",
        "https://www.hornbach.ro",
        "https://www.hornbach.se",
        "https://www.hornbach.sk",
    ]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        client_config = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "OIDC_CLIENT_CONFIG")]/text()').get()
        )
        locale = client_config.get("ui_locales")
        company_code = client_config.get("companyCode")
        if locale and company_code:
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
