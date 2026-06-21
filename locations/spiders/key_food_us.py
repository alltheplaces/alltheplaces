from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import bbox_contains, country_iseadgg_centroids
from locations.hours import OpeningHours


class KeyFoodUSSpider(Spider):
    name = "key_food_us"
    allowed_domains = ["www.keyfood.com"]

    brands = {
        "Ernest Klein": {"brand": "Ernest Klein"},
        "Food Dynasty": {"brand": "Food Dynasty"},
        "Food Emporium": {"brand": "The Food Emporium"},
        "Food Universe": {"brand": "Food Universe"},
        "Gala Foods": {"brand": "Gala Foods"},
        "Gala Fresh": {"brand": "GalaFresh Farms"},
        "GalaFresh": {"brand": "GalaFresh Farms"},
        "Halsey Traders": {"brand": "Halsey Traders Market"},
        "Key Food Marketplace": {"brand": "Key Food Marketplace"},
        "Urban Market": {"brand": "Key Food Urban Marketplace"},
        "Tropical Supermarket": {"brand": "Tropical Supermarket"},
        "SuperFresh": {"brand": "SuperFresh"},
        "Key Food": {"brand": "Key Food", "brand_wikidata": "Q6398037"},
    }

    async def start(self) -> AsyncIterator[Request]:
        northeast_bbox = (-81.0, 38.0, -69.0, 45.0)  # Covers PA, NJ, NY, CT, MA, RI
        florida_bbox = (-88.0, 24.0, -79.0, 31.0)  # Covers Florida

        for lat, lon in country_iseadgg_centroids(["US"], 48):
            point = (lon, lat)
            # Only yield a request if the centroid falls inside our target regions
            if bbox_contains(northeast_bbox, point) or bbox_contains(florida_bbox, point):
                url = f"https://www.keyfood.com/?lat={lat}&lng={lon}&miles=30&_data=root"
                yield JsonRequest(url=url)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().get("storeList", {}).get("stores", []):
            location = store.get("location", {})
            item = DictParser.parse(location)
            item["ref"] = store.get("storeId")
            item["name"] = (store.get("displayName") or "").removesuffix(item.get("street_address") or "").strip()

            if phones := store.get("phoneNumbers", []):
                item["phone"] = phones[0].get("value")

            found_match = False
            for b_key, b_data in self.brands.items():
                if b_key.lower() in item["name"].lower():
                    item.update(b_data)
                    found_match = True
                    break

            if not found_match:
                item.update(self.brands["Key Food"])

            apply_category(Categories.SHOP_SUPERMARKET, item)

            item["opening_hours"] = OpeningHours()
            weekly_hours = store.get("hours", {}).get("weekly", [])
            for day_hours in weekly_hours:
                day_name = day_hours.get("day")
                if not day_name:
                    continue

                daily = day_hours.get("daily", {})
                h_type = daily.get("type")

                if h_type == "OPEN_24_HOURS":
                    item["opening_hours"].add_range(day_name.title(), "00:00", "23:59")
                elif h_type == "OPEN":
                    open_time = daily.get("open", {}).get("open")
                    close_time = daily.get("open", {}).get("close")
                    if open_time and close_time:
                        item["opening_hours"].add_range(day_name.title(), open_time[:5], close_time[:5])

            yield item
