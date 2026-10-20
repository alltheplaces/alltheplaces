import re
from collections import Counter
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.communico import CommunicoSpider

BRANCH_URL = "https://www.lapl.org/branches/{}"
# Branches whose "about_url" is empty, points at the branch index, or (Cahuenga)
# at another branch's page. Slugs checked against lapl.org.
BRANCH_PAGES = {
    "4413": "cahuenga",
    "4419": "cypress-park",
    "4420": "durant",
    "4422": "echo-park",
    "4426": "encino-tarzana",
    "4433": "jefferson",
    "4438": "lincoln-heights",
    "4469": "vermont-square",
    "4471": "washington-irving",
}
WIFI_REGEX = re.compile(r"\bwi-?fi\b", re.IGNORECASE)


class LosAngelesPublicLibraryUSSpider(CommunicoSpider):
    name = "los_angeles_public_library_us"
    item_attributes = {"operator": "Los Angeles Public Library", "operator_wikidata": "Q4817385"}
    communico_client = "lapl"
    duplicate_images: set[str]

    def parse(self, response: TextResponse, opening_hours: dict, **kwargs) -> Iterable[Feature]:
        self.duplicate_images = {
            image
            for image, count in Counter(location.get("image") for location in response.json()).items()
            if image and count > 1
        }
        yield from super().parse(response, opening_hours, **kwargs)

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if slug := BRANCH_PAGES.get(location["id"]):
            item["website"] = BRANCH_URL.format(slug)
        if location.get("image") in self.duplicate_images:
            item["image"] = None
        # e.g. "Resources &amp; Services:&nbsp;Chromebooks, …, Wi-Fi, …"
        if WIFI_REGEX.search(location.get("description") or ""):
            apply_yes_no(Extras.WIFI, item, True)

        apply_category(Categories.LIBRARY, item)

        yield item
