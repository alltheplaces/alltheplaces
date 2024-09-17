from typing import Any, Iterable

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# A less common wordpress based storefinder, characterised by
# - POST of search params to "action": "get_stores",
# - Two letter variables in the results, like "na"
#
# To use, specify `domain` and `lat`, `lon` as the start point.
# TODO: Rename this spider when we identify the storelocator


class WordpressHeronFoodsSpider(Spider):
    domain = None
    radius = 600
    lat = None
    lon = None
    detected_rules = (
        []
    )  # DetectionRequestRule(https://{self.domain}/wp-admin/admin-ajax.php, but its a POST and has get_stores), or DetectionResponseRule(jsblob with na zp lng lon ID)

    def start_requests(self):
        yield FormRequest(
            url=f"https://{self.domain}/wp-admin/admin-ajax.php",
            formdata={
                "action": "get_stores",
                "lat": str(self.lat),
                "lng": str(self.lon),
                "radius": str(self.radius),
            },
            callback=self.parse,
            headers={"Referer": f"https://{self.domain}/storelocator/"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().values():
            self.pre_process_data(store)

            item = Feature(
                ref=store["ID"],
                lat=store["lat"],
                lon=store["lng"],
                branch=store["na"],
                street_address=store["st"].replace("<br>", ", "),
                city=store["ct"].strip(),
                postcode=store["zp"].strip(),
                website=store["gu"],
            )

            try:
                item["opening_hours"] = self.pares_opening_hours(store)
            except:
                self.logger.error("Error parsing opening hours")
                self.crawler.stats.inc_value("{}/opening_hours/parse_error".format(self.name))

            yield from self.post_process_item(item, response, store)

    def pares_opening_hours(self, feature: dict) -> OpeningHours | None:
        if not feature.get("op"):
            return None
        oh = OpeningHours()

        for day in range(0, 7):
            start_time = feature["op"][str(day * 2)]
            end_time = feature["op"][str(day * 2 + 1)]
            if start_time in ["Fermé"]:
                oh.set_closed(DAYS[day])
            else:
                oh.add_range(DAYS[day], start_time.replace(".", ":"), end_time.replace(".", ":"))

        return oh

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
