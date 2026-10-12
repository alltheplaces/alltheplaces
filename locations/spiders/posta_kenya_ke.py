from collections import Counter
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class PostaKenyaKESpider(AgileStoreLocatorSpider):
    name = "posta_kenya_ke"
    item_attributes = {"operator": "Posta Kenya", "operator_wikidata": "Q7233983"}
    allowed_domains = ["posta.co.ke"]  # https://posta.co.ke/post-offices/

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        # Offices without a real position are put on a shared placeholder point (79 offices from all over the
        # country on one spot in Nairobi, 6 on one spot in Mombasa), so a point used by several offices is dropped.
        points = Counter((feature.get("lat"), feature.get("lng")) for feature in response.json())
        self.shared_points = {point for point, count in points.items() if count > 1}
        yield from super().parse(response)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        # "city" holds the county (e.g. "Kisumu" for Ahero), sometimes two of them ("Kilifi/Mombasa").
        item["state"] = item.pop("city").strip() or None
        # "postal_code" is the office's own postcode (e.g. 40101 for Ahero), which is also its delivery area's.
        if (feature.get("lat"), feature.get("lng")) in self.shared_points:
            item["lat"] = item["lon"] = None
            self.crawler.stats.inc_value("atp/posta_kenya_ke/shared_point_dropped")
        elif item.get("lat") and item.get("lon") and -5 < float(item["lon"]) < 6 and 33 < float(item["lat"]) < 42:
            item["lat"], item["lon"] = item["lon"], item["lat"]  # a few offices have latitude and longitude swapped
        apply_category(Categories.POST_OFFICE, item)
        yield item
