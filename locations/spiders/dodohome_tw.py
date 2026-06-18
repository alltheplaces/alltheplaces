import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Selector, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class DodohomeTWSpider(Spider):
    name = "dodohome_tw"
    item_attributes = {"brand": "嘟嘟房", "brand_wikidata": "Q127693427"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.dodohome.com.tw/p2_parklist.aspx/SearchPark",
            data={
                "selPark": "all",
                "strLat": "",
                "strLng": "",
                "blnMobile": False,
                "blnTicket": False,
                "blnE_Ticket": False,
                "blnCreditFree": False,
            },
        )

    def parse(self, response: Response) -> Iterable[JsonRequest]:
        for park_id in Selector(text=response.json()["d"]).xpath('//*[@id="hiddenPark_ID"]/@value').get("").split(","):
            park_id = park_id.strip()
            yield JsonRequest(
                url="https://www.dodohome.com.tw/p2_parklist.aspx/SearchDetail",
                data={"park_id": park_id},
                callback=self.parse_location_details,
                cb_kwargs={"park_id": park_id},
            )

    def parse_location_details(self, response: Response, park_id: str) -> Any:
        location_details = response.json()["d"]
        item = Feature()
        item["ref"] = park_id
        item["addr_full"] = merge_address_lines(location_details[1:3])
        item["phone"] = location_details[3].replace(";", "; ").replace(",", "; ")
        item["lon"], item["lat"] = location_details[15], location_details[16]
        item["opening_hours"] = self.parse_opening_hours(location_details[4])

        if parking_type := location_details[6]:
            if "室外" in parking_type:
                item["extras"]["parking"] = "surface"
            elif "室內/車塔" in parking_type:
                item["extras"]["parking"] = "multi-storey"
            elif "室內" in parking_type:
                item["extras"]["building"] = "parking"
            elif "路邊/平面" in parking_type:
                item["extras"]["parking"] = "street_side"

        apply_category(Categories.PARKING, item)
        yield item

    def parse_opening_hours(self, hours: str) -> None | str | OpeningHours:
        if not hours:
            return None
        opening_hours = OpeningHours()
        if "24H" in hours:
            opening_hours = "24/7"
        elif match := re.match(r"(\d+:\d+)[-~](\d+:\d+)", hours):
            opening_hours.add_days_range(DAYS, *match.groups())
        else:
            self.logger.warning(f"Couldn't parse opening hours: {hours}")
        return opening_hours
