from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

API_URL = "https://www.lotteeatz.com/api/v1/stores/search?brandList=10&brandCodeList=LOTTERIA&page={}&size=100"


class LotteriaKRSpider(Spider):
    name = "lotteria_kr"
    item_attributes = {"brand": "롯데리아", "brand_wikidata": "Q249525"}
    start_urls = [API_URL.format(1)]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for store in data["content"]:
            if store["storeNm"].startswith("홈서비스"):
                continue  # Delivery-only virtual entries with no physical store
            item = Feature()
            item["ref"] = store["storecd"]
            item["branch"] = store["storeNm"]
            item["lat"] = store["geo"]["point"]["lat"]
            item["lon"] = store["geo"]["point"]["lng"]
            item["addr_full"] = merge_address_lines([store["adres"]["adres"], store["adres"]["detailAdres"]])
            item["phone"] = store["adres"]["telno"]

            # Many locations still carry stale 6-digit postcodes from the
            # system South Korea replaced with 5-digit codes in 2015.
            if len(postcode := (store["adres"]["zipNo"] or "").strip()) == 5:
                item["postcode"] = postcode

            if (open_time := store["operInfo"]["openTime"]) and (close_time := store["operInfo"]["closingTime"]):
                try:
                    item["opening_hours"] = OpeningHours()
                    item["opening_hours"].add_days_range(DAYS, open_time.strip(), close_time.strip(), "%H%M")
                except ValueError:
                    self.logger.debug(f"Couldn't parse opening hours: {open_time} - {close_time}")

            apply_yes_no(Extras.WIFI, item, store["svc"]["wifiUsePosblYn"] == "Y")
            apply_yes_no(Extras.DELIVERY, item, store["svc"]["homsvcYn"] == "Y", apply_positive_only=False)

            apply_category(Categories.FAST_FOOD, item)

            yield item

        if not data["last"]:
            yield Request(API_URL.format(data["pageNumber"] + 1))
