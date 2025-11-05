from copy import deepcopy
from typing import Any, AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AudiSpider(JSONBlobSpider):
    name = "audi"
    item_attributes = {"brand": "Audi", "brand_wikidata": "Q23317"}
    graphql_url = "https://dev-dealer-graphql.apps.emea.vwapps.io/"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"clientid": "d7sfqwrxzu"}, "ROBOTSTXT_OBEY": False}
    locations_key = ["data", "dealersByMarket", "dealers"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=self.graphql_url,
            method="POST",
            data={"query": "query MarketInfo { marketInfo { markets { market } } }"},
            callback=self.request_market_data,
        )

    def request_market_data(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        for market in response.json()["data"]["marketInfo"]["markets"]:
            yield JsonRequest(
                url=self.graphql_url,
                method="POST",
                data={
                    "variables": {"market": market["market"]},
                    "query": "query DealersByMarket($market: Market!) { dealersByMarket(market: $market) { dealers { country name region street houseNumber city dealerId brand services latitude longitude phone fax email url zipCode openingHours { openingHoursNote openingHoursFormatted departments { departmentName departmentOpeningHoursNote id openingHours { id open timeRanges { closeTime openTime } } } } } } }",
                },
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["dealerId"]
        if item.get("website") and not item["website"].startswith("http"):
            item["website"] = "https://" + item["website"]

        if "sales" in feature["services"] or "usedcars" in feature["services"]:
            shop_item = deepcopy(item)
            shop_item["ref"] = f"{item['ref']}-SHOP"
            try:
                shop_item["opening_hours"] = self.parse_hours(feature.get("openingHours"), ["sales", "0"])
            except Exception as e:
                self.logger.warning("Error parsing {} {}".format(feature.get("openingHours"), e))
            apply_category(Categories.SHOP_CAR, shop_item)
            yield shop_item

        if "service" in feature["services"]:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-SERVICE"
            try:
                service_item["opening_hours"] = self.parse_hours(feature.get("openingHours"), ["service", "1"])
            except Exception as e:
                self.logger.warning("Error parsing {} {}".format(feature.get("openingHours"), e))
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item

    def parse_hours(self, hours: dict, department_ids: list[str]) -> OpeningHours:
        oh = OpeningHours()
        departments = hours.get("departments", []) if hours else []
        for department in departments:
            if department.get("id") in department_ids:
                for day in department.get("openingHours", []):
                    if day["open"]:
                        open_time = day["timeRanges"][0]["openTime"]
                        close_time = day["timeRanges"][0]["closeTime"]
                        oh.add_range(day["id"], open_time, close_time, "%H:%M:%S")
                    else:
                        oh.set_closed(day["id"])
        return oh
