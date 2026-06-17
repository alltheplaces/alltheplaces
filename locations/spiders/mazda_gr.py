from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaGRSpider(Spider):
    """Base spider for Mazda dealer finders using the DNN 2sxc API."""

    name = "mazda_gr"
    item_attributes = MAZDA_SHARED_ATTRIBUTES

    # Subclasses must set these:
    api_url: str = "https://www.mazda.gr/api/2sxc/app/auto/query/DealerListByPortalAlias/Default"
    module_id: str = "22432"
    tab_id: str = "1527"
    country: str = "GR"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=self.api_url,
            headers={
                "ModuleId": self.module_id,
                "ContentBlockId": self.module_id,
                "TabId": self.tab_id,
                "PageId": self.tab_id,
            },
        )

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        for dealer in response.json().get("Default", []):
            if dealer.get("HasSales"):
                item = self._make_item(dealer)
                item["ref"] = str(dealer["Id"]) + "_Sales"
                apply_category(Categories.SHOP_CAR, item)
                yield item
            if dealer.get("HasRepair"):
                item = self._make_item(dealer)
                item["ref"] = str(dealer["Id"]) + "_Service"
                apply_category(Categories.SHOP_CAR_REPAIR, item)
                yield item
            if not dealer.get("HasSales") and not dealer.get("HasRepair"):
                item = self._make_item(dealer)
                item["ref"] = str(dealer["Id"])
                yield item

    def _make_item(self, dealer: dict) -> Feature:
        item = Feature()
        item["branch"] = dealer.get("Title")
        item["lat"] = dealer.get("Latitude")
        item["lon"] = dealer.get("Longitude")
        item["addr_full"] = dealer.get("Address")
        item["website"] = dealer.get("Website") or None
        item["country"] = self.country
        return item
