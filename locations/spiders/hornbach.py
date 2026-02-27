from typing import Any, Iterable

import chompjs
from scrapy.http import JsonRequest, Response, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HornbachSpider(JSONBlobSpider):
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
    custom_settings = {"DOWNLOAD_TIMEOUT": 180}

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
        yield from super().parse(response)

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("data"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("street")
        item["branch"] = item.pop("name").removeprefix("BODENHAUS ").removeprefix("HORNBACH ")
        if brand_info := self.BRANDS.get(feature["client"]):
            item.update(brand_info)
        if feature["client"] == "bodenhaus":
            apply_category(Categories.SHOP_FLOORING, item)

        item["opening_hours"] = self.parse_opening_hours(feature.get("simplifiedOpeningHours", []))
        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            start_day = rule.get("weekdayFrom")
            end_day = rule.get("weekdayTo") or start_day
            if start_day and end_day:
                oh.add_days_range(day_range(start_day, end_day), rule["timeFrom"], rule["timeTo"], "%H:%M:%S")
        return oh
