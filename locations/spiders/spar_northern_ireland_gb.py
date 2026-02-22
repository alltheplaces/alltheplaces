from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES


class SparNorthernIrelandGBSpider(Spider):
    name = "spar_northern_ireland_gb"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_requests(self, page: int) -> JsonRequest:
        return JsonRequest(
            f"https://www.spar-ni.co.uk/umbraco/api/storelocationapi/stores?pageNumber={page}", meta={"page": page}
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_requests(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["storeList"]:
            location["street_address"] = merge_address_lines(
                [location["Address1"], location["Address2"], location["Address3"]]
            )
            item = DictParser.parse(location)
            item["website"] = response.urljoin(location["StoreUrl"])

            if "EUROSPAR" in item["name"]:
                item["branch"] = item.pop("name").replace("EUROSPAR", "")
                item["name"] = "Eurospar"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            else:
                item["branch"] = item.pop("name").replace("SPAR", "")
                item["name"] = "Spar"
                apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item

        if len(response.json()["storeList"]) >= 10:
            yield self.make_requests(response.meta["page"] + 1)
