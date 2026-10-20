from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class GoldenChickUSSpider(Where2GetItSpider):
    """
    Golden Chick's official locator (linked from goldenchick.com/locations/)
    is hosted by Where2GetIt at
    https://hosted.where2getit.com/goldenchick/index2014.html.
    """

    name = "golden_chick_us"
    item_attributes = {"brand": "Golden Chick", "brand_wikidata": "Q3772930"}
    api_brand_name = "goldenchick"
    api_key = "D4DD3370-A5F3-11E1-AEA5-E52BA958831C"
    api_filter = {"country": {"eq": "US"}}

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        if location.get("country") != "US":
            return

        item["ref"] = location.get("clientkey")
        item["branch"] = self.clean_branch(location.get("name"))
        item.pop("name", None)
        item["website"] = location.get("website")

        oh = OpeningHours()
        for day in DAYS_FULL:
            open_time = location.get("{}_open".format(day.lower()))
            close_time = location.get("{}_close".format(day.lower()))
            if open_time and close_time:
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh

        apply_category(Categories.FAST_FOOD, item)

        yield item

    @staticmethod
    def clean_branch(name: str | None) -> str | None:
        """Names are formatted "Golden Chick #1427 Lake Charles, LA (Ryan St)"."""
        if not name:
            return None
        branch = name.removeprefix("Golden Chick").strip()
        if branch.startswith("#"):
            branch = branch.split(" ", 1)[-1]
        return branch.strip() or None
