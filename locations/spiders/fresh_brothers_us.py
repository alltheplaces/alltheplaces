import re
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class FreshBrothersUSSpider(StructuredDataSpider):
    name = "fresh_brothers_us"
    item_attributes = {"brand": "Fresh Brothers"}
    allowed_domains = ["freshbrothers.com"]
    start_urls = ["https://freshbrothers.com/locations/"]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_email = False
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in sorted(set(response.xpath("//a/@href").re(r"^/locations/[a-z0-9-]+/$"))):
            yield response.follow(path, callback=self.parse_sd)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        # "Fresh Brothers Beverly Hills"
        item["branch"] = (item.pop("name", None) or "").removeprefix("Fresh Brothers").strip()
        item["website"] = response.url

        for link in response.xpath('//a[contains(@href, "google.com/maps/place")]/@href').getall():
            if coordinates := re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", link):
                item["lat"], item["lon"] = coordinates.groups()
                break

        item["opening_hours"] = self.parse_opening_hours(ld_data.get("openingHoursSpecification") or [])

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"

        yield item

    @staticmethod
    def parse_opening_hours(specification: list[dict]) -> OpeningHours | None:
        """Each rule is {"dayOfWeek": "Sunday", "description": "10:30am-9pm"}."""
        oh = OpeningHours()

        for rule in specification:
            if not (day := DAYS_EN.get((rule.get("dayOfWeek") or "").strip())):
                continue

            hours = (rule.get("description") or "").replace("\u2013", "-").replace("\u2014", "-")
            if not (
                times := re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", hours, re.I)
            ):
                continue

            oh.add_range(
                day,
                times.group(1),
                times.group(2),
                time_format=["%I:%M%p", "%I:%M %p", "%I%p", "%I %p"],
            )

        return oh if oh else None
