from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids


class ZaxbysUSSpider(Spider):
    name = "zaxbys_us"
    item_attributes = {"brand": "Zaxby's", "brand_wikidata": "Q8067525"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids("US", 94):
            yield JsonRequest(
                url=f"https://zapi.zaxbys.com/v1/stores/near?latitude={lat}&longitude={lon}&radius=100&limit=100",
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full", None)
            item["branch"] = item.pop("name").split(" -")[0]
            item[
                "website"
            ] = f'https://www.zaxbys.com/locations/{store["state"]}/{store["city"]}/{store["slug"]}'.lower().replace(
                " ", "-"
            )
            apply_yes_no(Extras.DELIVERY, item, store.get("supportsDelivery"))
            apply_yes_no(Extras.TAKEAWAY, item, store.get("supportsPickup"))
            apply_yes_no(Extras.INDOOR_SEATING, item, store.get("supportsDineIn"))
            apply_yes_no(Extras.DRIVE_THROUGH, item, store.get("supportsDriveThru"))
            apply_yes_no(Extras.WIFI, item, store.get("freeWifi"))
            yield item
