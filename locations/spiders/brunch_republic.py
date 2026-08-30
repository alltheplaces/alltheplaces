import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy.http import Request, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_IT, NAMED_DAY_RANGES_IT, OpeningHours
from locations.items import Feature


class BrunchRepublicSpider(Spider):
    name = "brunch_republic"
    item_attributes = {"brand": "Brunch Republic", "brand_wikidata": "Q140876630"}
    allowed_domains = ["brunchrepublic.com", "google.com", "goo.gl", "google.it"]
    start_urls = ["https://brunchrepublic.com/wp-json/wp/v2/location?per_page=100"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for loc in response.json():
            yield Request(
                loc["link"],
                callback=self.parse_location,
                cb_kwargs={"loc_id": str(loc["id"]), "loc_title": loc["title"]["rendered"]},
            )

    def parse_location(self, response: Response, loc_id: str, loc_title: str) -> Iterable[Any]:
        item = Feature()
        item["ref"] = loc_id
        item["website"] = response.url
        item["branch"] = loc_title

        for h5 in response.xpath("//h5"):
            h5_text = "".join(h5.xpath(".//text()").getall()).lower()
            if "contatti" in h5_text:
                if p_text := "".join(h5.xpath("./following::p[1]//text()").getall()).strip():
                    item["phone"] = p_text
            elif "indirizzo" in h5_text:
                if addr_text := "".join(h5.xpath("./following::p[1]//text()").getall()).strip():
                    item["addr_full"] = addr_text
            elif "orari" in h5_text:
                oh = OpeningHours()
                p_elements = h5.xpath(
                    './following::p[preceding::h5[1][contains(translate(., "ORARI", "orari"), "orari")]]'
                )
                for p in p_elements:
                    t = "".join(p.xpath(".//text()").getall()).strip()
                    if t and ("|" in t or "-" in t or ":" in t):
                        cleaned = t.replace("|", " ").replace(".", ":")
                        try:
                            oh.add_ranges_from_string(cleaned, days=DAYS_IT, named_day_ranges=NAMED_DAY_RANGES_IT)
                        except Exception:
                            pass
                item["opening_hours"] = oh.as_opening_hours()

        apply_category(Categories.RESTAURANT, item)
        apply_category({"cuisine": "brunch"}, item)

        map_href = response.xpath(
            '//a[contains(@href, "maps.app.goo.gl") or contains(@href, "goo.gl/maps") or contains(@href, "google.com/maps")]/@href'
        ).get()

        if map_href:
            yield Request(
                map_href,
                callback=self.parse_map_link,
                cb_kwargs={"item": item},
                dont_filter=True,
            )
        else:
            yield item

    def parse_map_link(self, response: Response, item: Feature) -> Iterable[Feature]:
        lat, lon = self._extract_coords(response.url)
        if lat is None:
            for redirect in response.meta.get("redirect_urls", []):
                lat, lon = self._extract_coords(unquote(redirect))
                if lat is not None:
                    break

        item["lat"] = lat
        item["lon"] = lon
        yield item

    @staticmethod
    def _extract_coords(url: str):
        url = unquote(url)
        if m := re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", url):
            return float(m.group(1)), float(m.group(2))
        if m := re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url):
            return float(m.group(1)), float(m.group(2))
        if m := re.search(r"/search/(-?\d+\.\d+),\+?(-?\d+\.\d+)", url):
            return float(m.group(1)), float(m.group(2))
        if m := re.search(r"[?&](?:q|sll|ll|center)=(-?\d+\.\d+),(-?\d+\.\d+)", url):
            return float(m.group(1)), float(m.group(2))
        return None, None
