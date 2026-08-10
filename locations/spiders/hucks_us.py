import re
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class HucksUSSpider(Spider):
    """Spider for Huck's Food & Fuel US convenience stores/fuel stations.
    Closes #6082
    """

    name = "hucks_us"
    item_attributes = {"brand": "Huck's Food & Fuel", "brand_wikidata": "Q56276328"}
    start_urls = ["https://hucks.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for location in response.css("div.container.location"):
            street_address = location.css("div.font-weight-bold::text").get("").strip()

            raw_texts = location.css("div.col-sm-6.col-md.my-auto").xpath("text()").getall()
            raw_texts = [t.strip() for t in raw_texts if t.strip()]

            city = state = postcode = phone = ""
            for raw in raw_texts:
                if m := re.match(r"^(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", raw):
                    city, state, postcode = m.group(1).strip(), m.group(2), m.group(3)
                elif re.match(r"\(\d{3}\)\s*\d{3}-\d{4}", raw):
                    phone = raw

            map_anchor = location.css("a.show-on-map")
            lat = map_anchor.attrib.get("data-latitude")
            lon = map_anchor.attrib.get("data-longitude")

            detail_href = location.css("a[href]:not([data-latitude])::attr(href)").get("")
            detail_href = detail_href.strip().strip("/")
            ref = detail_href.split("/")[-1] if detail_href else None

            item = Feature()
            item["ref"] = ref
            item["street_address"] = street_address or None
            item["city"] = city or None
            item["state"] = state or None
            item["postcode"] = postcode or None
            item["phone"] = phone or None
            item["lat"] = float(lat) if lat else None
            item["lon"] = float(lon) if lon else None
            item["website"] = response.urljoin(detail_href + "/") if detail_href else None
            apply_category(Categories.FUEL_STATION, item)
            item["extras"]["shop"] = "convenience"

            if ref:
                yield Request(
                    url=response.urljoin(detail_href + "/"),
                    callback=self.parse_detail,
                    cb_kwargs={"item": item},
                )
            else:
                yield item

    def parse_detail(self, response: Response, item: Feature) -> Iterable[Feature]:
        # Hours text is inside a div.location-citystatezip containing <strong>Hours:</strong>
        for block in response.css("div.location-citystatezip"):
            if "Hours" in (block.css("strong::text").get() or ""):
                hours_text = block.xpath("normalize-space(.)").get("").replace("Hours:", "").strip()
                if hours_text:
                    oh = OpeningHours()
                    oh.add_ranges_from_string(hours_text)
                    item["opening_hours"] = oh
                break

        if not item.get("phone"):
            if phone := response.css("a[href^='tel']::attr(href)").get():
                item["phone"] = phone.replace("tel:", "").strip()

        yield item
