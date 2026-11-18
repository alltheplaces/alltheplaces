from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import postal_regions
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class WinnDixieUSSpider(Spider):
    name = "winn_dixie_us"
    item_attributes = {"brand": "Winn-Dixie", "brand_wikidata": "Q1264366"}
    allowed_domains = ["www.winndixie.com"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    states = {"FL", "AL", "LA", "MS"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for region in postal_regions("US", min_population=50000, consolidate_cities=True):
            if region["state"] not in self.states:
                continue
            yield JsonRequest(
                url=f"https://www.winndixie.com/api/seg/locator/stores?search={region['postal_region']}&miles=100"
            )

    def parse(self, response: Response) -> Iterable[Feature]:
        data = response.json()
        if not isinstance(data, list):
            self.logger.warning(f"Unexpected response for {response.url}: {response.text[:300]}")
            return

        for feature in data:
            item = DictParser.parse(feature)
            item["branch"] = item.pop("name", None)
            item["street_address"] = clean_address(
                [feature["address"].get("addressLine1"), feature["address"].get("addressLine2")]
            )
            item["opening_hours"] = OpeningHours()
            if hours := feature.get("workingHours"):
                item["opening_hours"].add_ranges_from_string(hours)

            if item.get("city") and item.get("state"):
                item["website"] = (
                    f"https://{self.allowed_domains[0]}/storedetails/"
                    f"{item['city'].lower().replace(' ', '-')}/{item['state'].lower()}?search={item['ref']}"
                )

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
