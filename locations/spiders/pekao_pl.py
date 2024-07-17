from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class PekaoPLSpider(Spider):
    name = "pekao_pl"
    item_attributes = {"brand_wikidata": "Q806642"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(url="https://www.pekao.com.pl/.rest/atms", callback=self.parse_atms)
        yield JsonRequest(
            url="https://www.pekao.com.pl/.rest/branches?clientType=INDIVIDUAL", callback=self.parse_banks
        )

    def parse_atms(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["ref"] = location["atmItemId"]
            item["lat"] = location["lt"]
            item["lon"] = location["lg"]

            # More details available at
            # "https://www.pekao.com.pl/.rest/atms/{}".format(location["id"])

            apply_category(Categories.ATM, item)

            yield item

    def parse_banks(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if location["t"] == "PARTNER_BRANCH":
                continue
            item = Feature()
            item["ref"] = location["branchItemId"]
            item["lat"] = location["lt"]
            item["lon"] = location["lg"]

            # More details available at
            # "https://www.pekao.com.pl/.rest/branches/{}".format(location["id"])

            apply_category(Categories.BANK, item)

            yield item
