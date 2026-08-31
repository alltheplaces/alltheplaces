import re
from typing import Any

import scrapy
from parsel import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_IT, OpeningHours
from locations.items import Feature


class SpontiniSpider(scrapy.Spider):
    name = "spontini"
    item_attributes = {"brand": "Spontini", "brand_wikidata": "Q105643882"}
    start_urls = ["https://spontinimilano.com/pizzerie/"]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield scrapy.Request(
            "https://spontinimilano.com/markers_json_load.php",
            method="POST",
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://spontinimilano.com/pizzerie/",
            },
            callback=self.parse_markers,
        )

    def parse_markers(self, response: Response, **kwargs: Any) -> Any:
        seen_refs = set()
        for store in response.json():
            try:
                lat = float(store.get("lat"))
                lon = float(store.get("lng"))
            except (ValueError, TypeError):
                continue

            if lat == 0 and lon == 0:
                continue

            url_slug = store.get("url", "").strip()
            ref = url_slug or store.get("name", "").strip()
            if ref in seen_refs:
                continue
            seen_refs.add(ref)

            item = Feature()
            item["ref"] = ref
            item["lat"] = lat
            item["lon"] = lon
            item["branch"] = store.get("name", "").strip().title()

            if raw_addr := store.get("sommario"):
                addr = " ".join(Selector(text=raw_addr).xpath("//text()").getall())
                item["street_address"] = re.sub(r"\s+", " ", addr).strip(" ,-") or None

            if phone := store.get("telefono_locale"):
                if phone.strip(" -"):
                    item["phone"] = phone.strip()

            if url_slug:
                item["website"] = f"https://spontinimilano.com/pizzerie/{url_slug}/"
            else:
                item["website"] = "https://spontinimilano.com/pizzerie/"

            apply_category(Categories.FAST_FOOD, item)
            apply_category({"cuisine": "pizza"}, item)

            if url_slug:
                yield scrapy.Request(
                    item["website"],
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
        oh = OpeningHours()
        p_elems = response.xpath(
            '//h2[contains(translate(text(), "ORARI", "orari"), "orari")]/following-sibling::div[1]//p'
        )
        for p in p_elems:
            text = " ".join(p.xpath(".//text()").getall())
            cleaned = text.replace(".", ":")
            cleaned = re.sub(r"\b24:(\d{2})\b", r"00:\1", cleaned)
            cleaned = re.sub(r"(\d{1,2}:\d{2})\s*/\s*(\d{1,2}:\d{2})", r"\1 - \2", cleaned)
            cleaned = cleaned.replace(" / ", ", ")
            try:
                oh.add_ranges_from_string(cleaned, days=DAYS_IT)
            except Exception:
                pass

        if oh.as_opening_hours():
            item["opening_hours"] = oh

        yield item
