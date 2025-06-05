from typing import Any

import scrapy
import xmltodict
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class OttosCHSpider(scrapy.Spider):
    name = "ottos_ch"
    item_attributes = {"brand": "Otto's", "brand_wikidata": "Q2041507"}
    start_urls = [
        "https://api.ottos.ch/occ/v2/ottos/stores?fields=stores(additionalOpeningInformation,name,displayName,formattedDistance,openingHours(weekDayOpeningList(FULL),specialDayOpeningList(FULL)),geoPoint(latitude,longitude),address(line1,line2,town,region(FULL),postalCode,phone,country,email),features,todaySchedule(DEFAULT),storeFeatures(code,name,tooltip)),pagination(DEFAULT),sorts(DEFAULT),selectableStoreFeatures,selectedStoreFeature,selectableStoreDistances,selectedStoreDistance&query=&radius=10000&lang=de&curr=CHF"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in DictParser.get_nested_key(xmltodict.parse(response.text), "stores"):
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item["ref"] = item.pop("name")
            if state := item.get("state"):
                item["state"] = state["isocodeShort"]
            item["street_address"] = merge_address_lines([store.get("line1"), store.get("line2")])
            item["opening_hours"] = OpeningHours()
            for day_time in store["openingHours"]["weekDayOpeningList"]:
                if day_time["closed"] == "true":
                    item["opening_hours"].set_closed(day_time["weekDay"])
                else:
                    item["opening_hours"].add_range(
                        day_time["weekDay"],
                        day_time["openingTime"]["formattedHour"],
                        day_time["closingTime"]["formattedHour"],
                    )

            if store["displayName"].startswith("OTTO'S Beauty Shop "):
                item["branch"] = store["displayName"].removeprefix("OTTO'S Beauty Shop ")
                item["name"] = "Otto's Beauty Shop"
                apply_category(Categories.SHOP_COSMETICS, item)
            elif store["displayName"].startswith("OTTO'S Sport Outlet "):
                item["branch"] = store["displayName"].removeprefix("OTTO'S Sport Outlet ")
                item["name"] = "Otto's Sport Outlet"
                apply_category(Categories.SHOP_SPORTS, item)
            elif store["displayName"].startswith("OTTO'S mini "):
                item["branch"] = store["displayName"].removeprefix("OTTO'S mini ")
                item["name"] = "Otto's mini"
                apply_category(Categories.SHOP_VARIETY_STORE, item)
            else:
                item["branch"] = store["displayName"].removeprefix("OTTO'S ")
                apply_category(Categories.SHOP_VARIETY_STORE, item)

            yield item
