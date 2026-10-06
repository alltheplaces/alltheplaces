from collections import Counter
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TanzaniaPostsTZSpider(Spider):
    name = "tanzania_posts_tz"
    item_attributes = {"operator": "Tanzania Posts Corporation", "operator_wikidata": "Q7684130"}
    allowed_domains = ["www.posta.co.tz"]
    # Feed behind the "nearest branch" map at https://www.posta.co.tz/nearest-branch/
    start_urls = ["https://www.posta.co.tz/sw/api_branches/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        branches = {}
        for branch in response.json():
            ref = "{}-{}".format(branch["region"], branch["branch_name"].strip())
            # A few branches are listed twice, once with and once without coordinates.
            if ref not in branches or not branches[ref].get("latitude"):
                branches[ref] = branch

        coords = {ref: self.clean_coords(b.get("latitude"), b.get("longtude")) for ref, b in branches.items()}
        # Several unrelated branches (e.g. Babati and Arusha HPO, Wete and Zanzibar HPO) share one
        # coordinate pair; those positions are placeholders, so drop them rather than mislocate.
        stacked = Counter(c for c in coords.values() if c)

        for ref, branch in branches.items():
            item = Feature()
            item["ref"] = ref
            item["branch"] = branch["branch_name"].strip()
            item["extras"]["addr:region:code"] = str(branch["region"])  # numeric id, no name lookup exposed
            if (c := coords[ref]) and stacked[c] == 1:
                item["lat"], item["lon"] = c
            item["country"] = "TZ"
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def clean_coords(lat: str | None, lon: str | None) -> tuple[float, float] | None:
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            return None
        if 0.9 < lat < 11.8 and 29.3 < lon < 40.5:
            lat = -lat  # a few Dodoma branches are missing the minus sign on the latitude
        if not (-11.8 < lat < -0.9 and 29.3 < lon < 40.5):
            return None
        return lat, lon
