import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_IT, DAYS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.items import Feature


class RossopomodoroSpider(scrapy.Spider):
    name = "rossopomodoro"
    item_attributes = {"brand": "Rossopomodoro", "brand_wikidata": "Q16598843"}
    start_urls = [
        "https://www.rossopomodoro.it/web/ajaxUtils/documentHelper.aspx?opc=pv_near&distance=&lat=&lng=&address="
    ]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for marker in data.get("Markers", []):
            try:
                lat = float(marker.get("latitude"))
                lon = float(marker.get("longitude"))
            except (ValueError, TypeError):
                continue

            if lat == 0 and lon == 0:
                continue

            item = Feature()
            item["ref"] = str(marker.get("mId") or marker.get("IdDocument"))
            item["lat"] = lat
            item["lon"] = lon

            title = marker.get("title", "").strip()
            item["branch"] = title.removeprefix("Rossopomodoro").strip(" -") or None
            item["street_address"] = marker.get("m_address") or marker.get("address")
            item["website"] = marker.get("href")

            apply_category(Categories.RESTAURANT, item)
            apply_category({"cuisine": "pizza;italian"}, item)

            if href := marker.get("href"):
                yield scrapy.Request(
                    href,
                    callback=self.parse_store,
                    cb_kwargs={"item": item},
                    errback=self.handle_error,
                    meta={"item": item},
                )
            else:
                yield item

    def handle_error(self, failure: Any) -> Any:
        if item := failure.request.meta.get("item"):
            yield item

    def parse_store(self, response: Response, item: Feature) -> Any:
        header_text = " ".join(response.xpath('//div[contains(@class, "col-9")]//text()').getall())
        if phone_match := re.search(r"-\s*([0-9\s/+]{6,})\s*$", header_text.strip()):
            phone = phone_match.group(1).strip()
            item["phone"] = phone

        oh = OpeningHours()
        for row in response.xpath('//table[contains(@class, "table-borderless")]//tr'):
            day = row.xpath("./th/text()").get()
            times = row.xpath("./td/text()").get()
            if day and times:
                try:
                    oh.add_ranges_from_string(
                        f"{day.strip()}: {times.strip()}",
                        days=DAYS_IT,
                        named_day_ranges=NAMED_DAY_RANGES_IT,
                        named_times=NAMED_TIMES_IT,
                        closed=CLOSED_IT,
                    )
                except Exception:
                    pass

        if oh.as_opening_hours():
            item["opening_hours"] = oh

        yield item
