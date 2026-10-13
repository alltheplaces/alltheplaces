import re
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.structured_data_spider import StructuredDataSpider

# The locations page carries each restaurant's coordinates on its map bubble,
# which also links to the restaurant's page. Those pages hold a schema.org
# FoodEstablishment record with the address, phone and hours, but no geo, so
# the coordinates are carried over from the listing.
#
# The record's hours are written with seconds, and the restaurants that close
# at midnight give "00:00:00" rather than a 24 hour closing time.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class CityWorksUSSpider(StructuredDataSpider):
    name = "city_works_us"
    item_attributes = {"brand": "City Works Eatery & Pour House"}
    allowed_domains = ["www.cityworksrestaurant.com"]
    start_urls = ["https://www.cityworksrestaurant.com/locations/"]
    wanted_types = ["FoodEstablishment"]
    time_format = "%H:%M:%S"
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for bubble in response.xpath('//div[contains(@class, "oms_locations_bubble_data")]'):
            if not (url := bubble.xpath('.//h5[@class="title"]/a/@href').get()):
                continue

            yield response.follow(
                url,
                callback=self.parse_sd,
                meta={
                    "ref": bubble.xpath("@data-id").get(),
                    # "Watertown, MA"
                    "branch": re.sub(
                        r",\s*[A-Z]{2}$", "", (bubble.xpath('.//h5[@class="title"]/a/text()').get() or "").strip()
                    ),
                    "lat": bubble.xpath("@data-lat").get(),
                    "lon": bubble.xpath("@data-lng").get(),
                },
            )

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.meta.get("ref")
        item["branch"] = response.meta.get("branch")
        item["lat"] = response.meta.get("lat")
        item["lon"] = response.meta.get("lon")
        item["name"] = None
        item["website"] = response.url

        item["opening_hours"] = self.parse_opening_hours(ld_data.get("openingHoursSpecification") or [])

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "american"

        yield item

    @staticmethod
    def parse_opening_hours(specification: list[dict]) -> OpeningHours | None:
        """The times carry seconds, and a midnight closing is given as "00:00:00"."""
        oh = OpeningHours()

        for rule in specification:
            opens, closes = (rule.get("opens") or "")[:5], (rule.get("closes") or "")[:5]
            if not opens or not closes:
                continue
            if closes == "00:00":
                closes = "24:00"

            days = rule.get("dayOfWeek")
            for day in [days] if isinstance(days, str) else days or []:
                if day := DAYS_EN.get(day):
                    oh.add_range(day, opens, closes)

        return oh if oh else None
