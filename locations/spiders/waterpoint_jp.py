import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Vending, add_vending, apply_category
from locations.items import Feature


class WaterpointJPSpider(Spider):
    name = "waterpoint_jp"
    item_attributes = {"brand": "WaterPoint", "brand_wikidata": "Q135639331", "operator": "WaterPoint"}
    start_urls = ["https://waterpoint.co.jp/vm-c/"]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Each marker is structured as:
        # clusters.addLayer(L.marker([lat, lng], {
        #     icon: minIcon,
        #     title: 'NAME'
        # }).bindPopup("NAME</br>ADDRESS</br>..."));
        marker_pattern = re.compile(
            r"L\.marker\(\[(-?\d+\.\d+),\s*(-?\d+\.\d+)\][^)]*\)\s*" r"\.bindPopup\(\"([^\"]+)\"\)",
            re.DOTALL,
        )

        for i, match in enumerate(marker_pattern.finditer(response.text)):
            lat, lng, popup_html = match.group(1), match.group(2), match.group(3)

            # Popup format: "NAME</br>ADDRESS</br>機種 / TYPE</br>水 / WATER_TYPE</br><a ...>"
            # Split on </br> separator
            parts = [p.strip() for p in re.split(r"</?br/?>\s*|</?[Bb][Rr]\s*/?>\s*", popup_html)]
            parts = [p for p in parts if p and not p.startswith("<a ")]

            name = parts[0] if len(parts) > 0 else None
            street_address = parts[1] if len(parts) > 1 else None

            item = Feature()
            item["ref"] = str(i + 1)
            item["lat"] = float(lat)
            item["lon"] = float(lng)
            item["name"] = name
            item["street_address"] = street_address
            item["country"] = "JP"

            apply_category(Categories.VENDING_MACHINE, item)
            add_vending(Vending.WATER, item)

            yield item
