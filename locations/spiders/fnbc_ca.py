from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class FnbcCASpider(Spider):
    name = "fnbc_ca"
    FNBC = {"brand": "First Nations Bank of Canada", "brand_wikidata": "Q1419511"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url=f"https://api.forge.central1.cc/find-branch-atm-service/v1/places?latitude=58.55148693137242&longitude=-94.06979&radius=4000&type=all&dedupeAtms=true",
            headers={"c1-tid": "sk_fnbc"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location_type in ["branches", "atms"]:
            locations = response.json()[location_type]
            for location in locations:
                location.update(location.pop("details", {}))
                item = DictParser.parse(location)
                item["street_address"] = merge_address_lines(location["address"].get("line"))
                if location.get("type") == "branch":
                    item.update(self.FNBC)
                    apply_category(Categories.BANK, item)
                elif location.get("type") == "atm":
                    if item["name"] == self.FNBC["brand"]:
                        item.update(self.FNBC)
                    else:
                        # ATMs of other brands/operators
                        pass
                    apply_category(Categories.ATM, item)
                yield item
