from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_SI, OpeningHours


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

            oh = OpeningHours()
            for avail in poi.get("availabilities") or []:
                day = DAYS_SI.get(avail["dayOfWeek"])
                if not day:
                    continue
                for r in avail.get("range") or []:
                    if r.get("closed") or r.get("from") is None:
                        continue
                    # Times are formatted as "8.00" / "24.00" — normalise to "HH:MM"
                    open_time = r["from"].replace(".", ":").zfill(5)
                    close_time = r["to"].replace(".", ":").zfill(5)
                    oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh.as_opening_hours()

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
