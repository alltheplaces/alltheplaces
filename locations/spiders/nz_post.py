from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

# The NZ Post API truncates responses at 500 records, so the country
# extent is searched recursively: any bbox that hits the cap is split
# into four quadrants until each cell returns under it.
CATEGORY_MAP = {
    "PostShop": Categories.POST_OFFICE,
    "Third Party Partner": Categories.POST_OFFICE,  # Co-branded post office in third-party retailers
    "Postbox Lobby": Categories.POST_OFFICE,  # Private (PO) box lobby inside a partner store
    "Postbox": Categories.POST_BOX,
    "Depot": Categories.POST_DEPOT,
}


class NzPostSpider(Spider):
    name = "nz_post"
    item_attributes = {"operator": "New Zealand Post", "operator_wikidata": "Q1144511"}
    allowed_domains = ["api.nzpost.co.nz"]
    max_results = 500

    def bbox_request(self, lat1: float, lat2: float, lon1: float, lon2: float) -> Request:
        return Request(
            url=(
                "https://api.nzpost.co.nz/digital/postshop-locations/v2/locations"
                f'?type=MAP_EXTENT&value={{"latitude1":{lat1},"latitude2":{lat2},"longitude1":{lon1},"longitude2":{lon2}}}'
                f"&max={self.max_results}"
            ),
            cb_kwargs={"bbox": (lat1, lat2, lon1, lon2)},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.bbox_request(-34, -48, 165, 179)

    def parse(self, response: Response, bbox: tuple[float, float, float, float], **kwargs: Any) -> Any:
        locations = response.json().get("locations", [])

        if len(locations) >= self.max_results:
            lat1, lat2, lon1, lon2 = bbox
            lat_mid = (lat1 + lat2) / 2
            lon_mid = (lon1 + lon2) / 2
            yield self.bbox_request(lat1, lat_mid, lon1, lon_mid)
            yield self.bbox_request(lat1, lat_mid, lon_mid, lon2)
            yield self.bbox_request(lat_mid, lat2, lon1, lon_mid)
            yield self.bbox_request(lat_mid, lat2, lon_mid, lon2)
            return

        for location in locations:
            item = DictParser.parse(location)

            address_details = location.get("address_details") or {}
            item["street_address"] = address_details.get("address_line_1")
            item["city"] = address_details.get("city") or address_details.get("suburb")
            item["postcode"] = address_details.get("post_code")

            if category := CATEGORY_MAP.get(location.get("type")):
                apply_category(category, item)
            else:
                self.logger.error("Unexpected category: {}".format(location.get("type")))
                continue

            yield item
