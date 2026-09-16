from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class Cash2bitcoinUSSpider(JSONBlobSpider):
    name = "cash2bitcoin_us"
    item_attributes = {"brand": "Cash2Bitcoin", "brand_wikidata": "Q135318196"}
    allowed_domains = ["locations.cash2bitcoin.com"]

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://locations.cash2bitcoin.com/wp-json/geodir/v2/locations?per_page=100&page={page}",
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        yield from super().parse(response)
        if len(response.json()) == 100:
            yield self.make_request(response.meta["page"] + 1)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item.pop("name", None)
        item.pop("website", None)
        item.pop("phone", None)
        item["street_address"] = item.pop("street")
        item["image"] = feature["featured_image"]["src"]

        if business_hours := feature["business_hours"]:
            item["opening_hours"] = OpeningHours()
            for day in business_hours["rendered"]["days"].values():
                if day["closed"]:
                    item["opening_hours"].set_closed(day["day"])
                    continue
                for slot in day["slots"]:
                    item["opening_hours"].add_range(day["day"], *slot["slot"].split("-"))

        apply_category(Categories.ATM, item)
        item["extras"]["currency:XBT"] = "yes"
        item["extras"]["currency:ETH"] = "yes"
        item["extras"]["currency:LTC"] = "yes"
        item["extras"]["currency:USD"] = "yes"
        item["extras"]["cash_in"] = "yes"
        item["extras"]["cash_out"] = "no"
        yield item
