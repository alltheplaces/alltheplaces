from copy import deepcopy
from typing import AsyncIterator

import pycountry
from scrapy import Spider
from scrapy.http import JsonRequest, Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

FORD_SHARED_ATTRIBUTES = {"brand": "Ford", "brand_wikidata": "Q44294"}
LINCOLN_SHARED_ATTRIBUTES = {"brand": "Lincoln", "brand_wikidata": "Q216796"}


class FordSpider(Spider):
    name = "ford"
    brand_mapping = {
        "Ford": FORD_SHARED_ATTRIBUTES,
        "Lincoln": LINCOLN_SHARED_ATTRIBUTES,
        "Motorcraft": FORD_SHARED_ATTRIBUTES,
    }

    async def start(self) -> AsyncIterator[Request]:
        for country in pycountry.countries:
            if country.alpha_3 in ["USA", "CAN"]:  # included in ford_dealers_us and ford_ca using more accurate API
                continue
            url = f"https://www.ford.com/ecommsearch/non-secure/gep/ecom-search-dealer/api/public/{country.alpha_3}/dealers/search"
            yield JsonRequest(
                url=url,
                data={"latitude": 0, "longitude": 0, "radius": "99999", "unit": "mi", "count": "1000", "filters": ""},
                callback=self.parse_stores,
            )

    def parse_stores(self, response):
        results = response.json().get("dealers").get("results")
        for data in results:
            item = DictParser.parse(data)
            item["ref"] = data.get("EntityID")
            item["phone"] = data.get("PrimaryPhone")
            item["name"] = data.get("DealerName")
            item["country"] = data.get("CountryCode")
            item["opening_hours"] = self.parse_hours(data)
            self.repair_website(data["PrimaryURL"], item)

            if brand := self.brand_mapping[data.get("Brand")]:
                item.update(brand)
            else:
                self.logger.error(f"Unknown brand {data.get('Brand')} from {response.url}")

            is_sales = data["HasSalesDepartmentPV"] or data["HasSalesDepartmentCV"]
            is_service = data["HasServiceDepartmentPV"] or data["HasServiceDepartmentCV"]
            is_parts = data["HasPartsDepartment"]

            if is_sales:
                yield self.build_sales_item(item)
            if is_service:
                yield self.build_service_item(item)
            if not is_sales and not is_service and is_parts:
                yield self.build_parts_item(item)
            elif not is_sales and not is_service:
                # fallback category
                yield self.build_sales_item(item)

    def build_sales_item(self, item: Feature) -> Feature:
        sales_item = deepcopy(item)
        apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def build_service_item(self, item: Feature) -> Feature:
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-SERVICE"
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def build_parts_item(self, item: Feature) -> Feature:
        parts_item = deepcopy(item)
        parts_item["ref"] = f"{item['ref']}-PARTS"
        apply_category(Categories.SHOP_CAR_PARTS, parts_item)
        return parts_item

    def parse_hours(self, data: dict) -> OpeningHours | None:
        try:
            oh = OpeningHours()
            for day in DAYS_FULL:
                if opening_time := data.get(f"Sales{day}OpenTime"):
                    closing_time = data.get(f"Sales{day}CloseTime")
                    oh.add_range(day=day, open_time=opening_time, close_time=closing_time, time_format="%H%M")
            if oh.as_opening_hours():
                return oh
        except:
            return None

    def repair_website(self, website: str, item: Feature) -> None:
        try:
            if "http://" in website:
                website = website.replace("http://", "https://").split(" - ", 1)[0]
                item["website"] = website
            elif website.startswith("www."):
                website = website.replace("www.", "https://www.").split(" / ", 1)[0]
                item["website"] = website
            elif "@" in website:
                item["email"] = website
            elif website.startswith("ford-"):
                website = website.replace("ford-", "https://ford-")
                item["website"] = website
            elif website.startswith("https://"):
                item["website"] = website
        except:
            return None
