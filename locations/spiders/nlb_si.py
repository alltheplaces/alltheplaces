from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class NlbSISpider(Spider):
    name = "nlb_si"
    item_attributes = {"brand": "NLB", "brand_wikidata": "Q1481509"}

    async def start(self) -> AsyncIterator[Any]:
        for kind in ("atm", "branch"):
            yield Request(
                url=f"https://www.nlb.si/content/nlbbanks/nlbsi/sl/osebno/poslovalnice-in-bankomati/jcr:content/root/container/container/branchsearch.facilities.json?kind={kind}"
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json():
            item = DictParser.parse(poi)

            # DictParser does not flatten nested address objects, so override
            # the geo/address fields from the nested "location" dict manually.
            loc = poi.get("location") or {}
            item["lat"] = loc.get("latitude")
            item["lon"] = loc.get("longitude")
            item["street_address"] = loc.get("street")
            item["city"] = loc.get("city")

            if facility_url := poi.get("facilityPageUrl"):
                item["website"] = f"https://www.nlb.si{facility_url}"

            kind = poi.get("kind")
            if kind == "atm":
                apply_category(Categories.ATM, item)
            elif kind == "branch":
                item["branch"] = (item.pop("name", "") or "").removeprefix("Poslovalnica ").strip() or None
                apply_category(Categories.BANK, item)
            else:
                self.logger.error("Unexpected NLB kind: %s", kind)
                continue

            yield item
