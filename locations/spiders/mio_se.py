import re
from typing import Any

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class MioSESpider(Spider):
    name = "mio_se"
    item_attributes = {
        "brand": "Mio",
        "brand_wikidata": "Q1315348",
        "country": "SE",
    }
    allowed_domains = ["mio.se"]
    start_urls = ["https://www.mio.se/butiker"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for link in response.xpath('//a[starts-with(@href, "/butiker/") and string-length(@href) > 10]'):
            href = link.xpath("@href").get()
            if not href or href.strip("/") == "butiker":
                continue
            url = response.urljoin(href)
            yield Request(url=url, callback=self.parse_store)

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        name = response.xpath("//h1/text()").get()
        if name:
            item["name"] = name.strip()
        item["website"] = response.url
        item["ref"] = response.url.rstrip("/").split("/")[-1]

        text = response.text

        def _decode(s: str) -> str:
            if "\\u" in s:
                return s.encode("latin-1").decode("unicode_escape")
            return s

        addr_m = re.search(r'"address":"([^"]+)"', text)
        zip_m = re.search(r'"zipCode":"([^"]+)"', text)
        city_m = re.search(r'"city":"([^"]+)"', text)
        if addr_m:
            item["street_address"] = _decode(addr_m.group(1))
        if zip_m:
            item["postcode"] = zip_m.group(1)
        if city_m:
            item["city"] = _decode(city_m.group(1))
        if item.get("street_address") or item.get("city"):
            parts = [item.get("street_address"), item.get("postcode"), item.get("city")]
            item["addr_full"] = ", ".join(p for p in parts if p)

        loc_m = re.search(
            r'"location":\{"longitude":([-\d.]+),"latitude":([-\d.]+)\}',
            text,
        )
        if loc_m:
            item["lon"] = float(loc_m.group(1))
            item["lat"] = float(loc_m.group(2))
        else:
            extract_google_position(item, response)
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
