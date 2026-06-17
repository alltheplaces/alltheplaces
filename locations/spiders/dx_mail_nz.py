import re
from typing import Iterable
from urllib.parse import unquote

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class DxMailNZSpider(Spider):
    name = "dx_mail_nz"
    item_attributes = {
        "brand": "DX Mail",
        "brand_wikidata": "Q125635563",
        "country": "NZ",
    }
    start_urls = ["https://www.dxmail.co.nz/branch-locations/"]

    def parse(self, response: Response, **kwargs) -> Iterable[Request | Feature]:
        # Each branch is in a div.city_content_wrap with a data-city attribute
        for section in response.css("div.city_content_wrap"):
            city_class = section.attrib.get("class", "").split()[-1]

            title = section.css("h4.title::text").get("").strip()
            if not title:
                continue

            # Extract address paragraphs, splitting on <br> within each <p>
            addr_lines = []
            phone = None
            for p in section.css("div.address p"):
                raw_html = p.get()
                parts = re.split(r"<br\s*/?>", raw_html)
                parts = [re.sub(r"<[^>]+>", "", pt).strip() for pt in parts]
                parts = [pt for pt in parts if pt]
                for part in parts:
                    if part.startswith("DX Box"):
                        continue
                    if part.startswith("Phone:"):
                        phone = re.sub(r"Phone:\s*", "", part)
                        continue
                    if part.startswith("Note:"):
                        continue
                    addr_lines.append(part)

            # Extract Google Maps link for coordinates
            map_href = section.css("p.map_link a::attr(href)").get()

            item = Feature()
            item["ref"] = city_class
            item["branch"] = title
            item["phone"] = phone
            item["website"] = "https://www.dxmail.co.nz/branch-locations/"
            item["addr_full"] = merge_address_lines(addr_lines) if addr_lines else None

            apply_category(Categories.OFFICE_COURIER, item)

            if map_href and "maps.app.goo.gl" in map_href:
                # Short link: follow redirect to resolve coordinates
                yield Request(
                    map_href,
                    callback=self._parse_short_link,
                    cb_kwargs={"item": item},
                    dont_filter=True,
                )
            elif map_href:
                lat, lon = self._extract_coords(map_href)
                item["lat"] = lat
                item["lon"] = lon
                yield item
            else:
                # No map link - yield without coordinates only if we have an address
                if addr_lines:
                    yield item

    def _parse_short_link(self, response: Response, item: Feature) -> Iterable[Feature]:
        # The final URL after redirect contains coordinates
        final_url = response.url
        lat, lon = self._extract_coords(final_url)
        if lat is None:
            # Try the redirect chain
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
        # Format: /@lat,lon,zoom
        m = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if m:
            return float(m.group(1)), float(m.group(2))
        # Format: ?sll=lat,lon or ?ll=lat,lon
        m = re.search(r"[?&](?:sll|ll)=(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if m:
            return float(m.group(1)), float(m.group(2))
        # Format: ?q=lat,lon
        m = re.search(r"[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if m:
            return float(m.group(1)), float(m.group(2))
        return None, None
