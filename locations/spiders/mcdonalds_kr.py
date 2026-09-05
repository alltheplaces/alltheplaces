import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature, set_closed, set_lat_lon
from locations.user_agents import BROWSER_DEFAULT


class McdonaldsKRSpider(Spider):
    name = "mcdonalds_kr"
    item_attributes = {
        "brand": "McDonald's",
        "brand_wikidata": "Q38076",
        "country": "KR",
    }
    allowed_domains = ["www.mcdonalds.co.kr"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    start_urls = ["https://www.mcdonalds.co.kr/api/v1/kor/store/list?view_rows=1000&page=1"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        data = response.json()
        result_object = data.get("resultObject") or {}
        total_count = result_object.get("totalCount")
        stores = result_object.get("list") or []

        if total_count and len(stores) < total_count:
            self.logger.warning(f"Expected {total_count} stores but received {len(stores)}")

        for store in stores:
            item = Feature()
            item["ref"] = store["code"]
            item["branch"] = (store.get("korName") or "").removesuffix("점").strip()
            item["addr_full"] = store.get("loadKor")
            item["postcode"] = store.get("zipCode")
            item["city"] = store.get("gugunKor")
            item["state"] = store.get("sidoKor")
            item["country"] = "KR"
            item["website"] = "https://www.mcdonalds.co.kr/kor/store/main"

            if tel := store.get("tel1"):
                if tel != "--":
                    item["phone"] = tel

            try:
                lat = float(store["lat"])
                lon = float(store["lng"])
                # Fix verified data entry error where leading '1' was omitted (e.g. 26.698... -> 126.698...)
                if 20.0 < lon < 30.0:
                    lon += 100.0
                set_lat_lon(item, lat, lon)
            except (ValueError, TypeError):
                self.logger.warning(
                    f"Invalid coordinates for store {item['ref']}: {store.get('lat')}, {store.get('lng')}"
                )

            # Status 'T' represents temporary closure
            if store.get("status") == "T":
                set_closed(item)

            if hours := self.parse_hours(store.get("workTime")):
                item["opening_hours"] = hours

            services = {
                svc.get("engName"): svc.get("serviceStatus") == "Y" for svc in store.get("storeServiceList") or []
            }
            apply_yes_no(Extras.DRIVE_THROUGH, item, services.get("McDrive") or store.get("mcdriveYn") == "Y")
            apply_yes_no(Extras.DELIVERY, item, services.get("McDelivery") or bool(store.get("deliveryInfo")))
            apply_yes_no(Extras.PARKING, item, services.get("Parking") or store.get("parkInfo") == "P")

            apply_category(Categories.FAST_FOOD, item)

            yield item

    def parse_hours(self, work_time: str | None) -> OpeningHours | None:
        if not work_time:
            return None

        work_time = work_time.strip()
        if work_time in ("24시간", "00:00~24:00"):
            oh = OpeningHours()
            oh.add_days_range(DAYS, "00:00", "24:00")
            return oh

        if "~" in work_time:
            parts = work_time.split("~")
            if len(parts) == 2:
                start_time, end_time = parts[0].strip(), parts[1].strip()
                if re.match(r"^\d:\d{2}$", start_time):
                    start_time = f"0{start_time}"
                if re.match(r"^\d:\d{2}$", end_time):
                    end_time = f"0{end_time}"
                try:
                    oh = OpeningHours()
                    oh.add_days_range(DAYS, start_time, end_time)
                    return oh
                except Exception as e:
                    self.logger.debug(f"Couldn't parse hours '{work_time}': {e}")

        return None
