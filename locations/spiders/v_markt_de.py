import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class VMarktDESpider(Spider):
    """Spider for V-Markt supermarkets in Germany.
    Closes #9084
    """

    name = "v_markt_de"
    item_attributes = {"brand": "V-Markt", "brand_wikidata": "Q2523915"}
    start_urls = ["https://www.v-markt.de/standorte_vmarkt"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # Each store has a tab block keyed by data-id.
        # Extract all blocks between consecutive data-id attributes.
        blocks = re.findall(
            r'data-id="(\d+)"[^>]*>(.*?)(?=data-id="\d+"|$)',
            response.text,
            re.DOTALL,
        )
        # Build a map of data-id -> coords from the Google Maps direction links
        coords_map = {
            m.group(1): (m.group(2), m.group(3))
            for m in re.finditer(
                r'data-id="(\d+)".*?destination=\(([0-9.-]+),\s*([0-9.-]+)\)',
                response.text,
                re.DOTALL,
            )
        }
        # Build a map of data-id -> store name from tab-label divs
        names_map = {
            m.group(1): m.group(2).strip()
            for m in re.finditer(
                r'<div class="tab-label"[^>]*data-id="(\d+)"[^>]*>(.*?)</div>',
                response.text,
            )
        }

        seen = set()
        for store_id, content in blocks:
            if store_id in seen:
                continue
            seen.add(store_id)

            name = names_map.get(store_id, "")
            if not name:
                continue

            # Extract address paragraph (first <p>): "Street\nPostcode City"
            paras = [re.sub(r"<[^>]+>", "", p).strip() for p in re.findall(r"<p[^>]*>(.*?)</p>", content, re.DOTALL)]

            street_address = None
            city = None
            postcode = None
            phone = None

            for para in paras:
                if not para:
                    continue
                # Phone paragraph starts with "Telefon:"
                phone_m = re.match(r"Telefon:\s*(.+)", para)
                if phone_m:
                    phone = phone_m.group(1).strip()
                    continue
                # Address paragraph: "Street\nPostcode City"
                addr_m = re.match(r"(.+)\n(\d{5})\s+(.+)", para, re.DOTALL)
                if addr_m:
                    street_address = addr_m.group(1).strip()
                    postcode = addr_m.group(2)
                    city = addr_m.group(3).strip()

            item = Feature()
            item["ref"] = store_id
            # Strip brand prefix from name to get branch name
            item["branch"] = re.sub(r"^V-Markt\s*", "", name).strip() or None
            item["street_address"] = street_address
            item["city"] = city
            item["postcode"] = postcode
            item["country"] = "DE"
            item["phone"] = phone

            if store_id in coords_map:
                item["lat"], item["lon"] = coords_map[store_id]

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
