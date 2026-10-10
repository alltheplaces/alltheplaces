from typing import Any, AsyncIterator

from scrapy import Selector, Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BelforUSSpider(Spider):
    name = "belfor_us"
    item_attributes = {"brand": "Belfor", "brand_wikidata": "Q4882373"}
    allowed_domains = ["belfor.com"]

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://www.belfor.com/us/wp-admin/admin-ajax.php",
            formdata={"action": "get_markers", "type": "all"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        markers = {str(marker["pid"]): marker for marker in response.json()["data"]["markers"]}

        for card in Selector(text=response.json()["data"]["html"]).css("li.location-card"):
            ref = card.attrib.get("data-id")
            marker = markers.get(ref, {})

            lat, lon = marker.get("lat"), marker.get("lng")
            if isinstance(lat, str) and "," in lat:
                # A handful of locations have their lat/lng values duplicated and
                # concatenated into a single "lat, lng, lat, lng" string in both fields.
                lat, lon = (value.strip() for value in lat.split(",")[:2])

            item = DictParser.parse(
                {
                    "ref": ref,
                    "name": card.css(".card-content__title::text").get(default="").strip(),
                    "address": card.css(".-address .info::text").get(default="").strip().removesuffix(" US"),
                    "phone": card.css(".-phone a::text").get(),
                    "lat": lat,
                    "lon": lon,
                }
            )
            item["website"] = card.css(".card-actions a::attr(href)").get()

            apply_category(Categories.OFFICE_COMPANY, item)

            yield item
