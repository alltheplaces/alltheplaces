from typing import Any

import scrapy
import xmltodict
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines


class OttosCHSpider(scrapy.Spider):
    name = "ottos_ch"
    item_attributes = {"brand": "Otto's", "brand_wikidata": "Q2041507"}
    start_urls = [
        "https://api.ottos.ch/occ/v2/ottos/stores?fields=stores(additionalOpeningInformation%2Cname%2CdisplayName%2CformattedDistance%2CopeningHours(weekDayOpeningList(FULL)%2CspecialDayOpeningList(FULL))%2CgeoPoint(latitude%2Clongitude)%2Caddress(line1%2Cline2%2Ctown%2Cregion(FULL)%2CpostalCode%2Cphone%2Ccountry%2Cemail)%2Cfeatures%2CtodaySchedule(DEFAULT)%2CstoreFeatures(code%2Cname%2Ctooltip))%2Cpagination(DEFAULT)%2Csorts(DEFAULT)%2CselectableStoreFeatures%2CselectedStoreFeature%2CselectableStoreDistances%2CselectedStoreDistance&query=&radius=10000&lang=de&curr=CHF",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in xmltodict.parse(response.text)["StoreFinderSearchPageWsDTO"]["stores"]["stores"]:
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item["ref"] = item.pop("name")
            if state := item.get("state"):
                item["state"] = state["isocodeShort"]
            item["branch"] = store["displayName"].removeprefix("OTTO'S ")
            item["street_address"] = merge_address_lines([store["line1"], store["line2"]])
            item["opening_hours"] = OpeningHours()
            for day_time in store["openingHours"]["weekDayOpeningList"]["weekDayOpeningList"]:
                day = sanitise_day(day_time["weekDay"], DAYS_DE)
                if day_time["closed"] == "true":
                    item["opening_hours"].set_closed(day)
                else:
                    open_time = day_time["openingTime"]["formattedHour"]
                    close_time = day_time["closingTime"]["formattedHour"]
                    item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)

            yield item
