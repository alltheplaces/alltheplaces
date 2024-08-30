from typing import Iterable

from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.algolia import AlgoliaSpider


class LesComptoirsDeLaBioFRSpider(AlgoliaSpider):
    name = "les_comptoirs_de_la_bio_fr"
    item_attributes = {"brand": "Les Comptoirs de la Bio", "brand_wikidata": "Q120801428"}
    api_key = "7a46160ed01bb0af2c2af8d14b97f3c5"
    app_id = "0KNEMTBXX3"
    index_name = "CDLB_fr"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # TODO: This spider shares most of its code with OrangePLSpider, only differing in website,
        # branch, image, and time format. The storefinder websites also look the same. Consider
        # refactoring if you find a third example, or figure out what common software they use.
        item["street_address"] = clean_address([feature.pop("street1"), feature.pop("street2")])
        item["addr_full"] = clean_address(feature["formatted_address"])
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["country"] = feature["country"]["code"]
        item["city"] = feature["city"]["name"]
        item["website"] = f"https://magasins.lescomptoirsdelabio.fr/fr/{feature['url_location']}"
        item["branch"] = item.pop("name").removeprefix("Les Comptoirs de La Bio ")
        item["opening_hours"] = self.extract_opening_hours(feature)
        item["image"] = feature["pictures"][0]
        yield item

    def extract_opening_hours(self, feature: dict) -> OpeningHours:
        if hours := feature.get("formatted_opening_hours"):
            try:
                oh = OpeningHours()
                for day, hour in hours.items():
                    for times in hour:
                        oh.add_range(day, times.split("-")[0], times.split("-")[1], time_format="%H:%M")
                return oh
            except Exception as e:
                self.logger.warning(f"Failed to parse hours {hours}: {e}")
