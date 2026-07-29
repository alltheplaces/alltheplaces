from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class StrackAndVanTilUSSpider(JSONBlobSpider):
    name = "strack_and_van_til_us"
    item_attributes = {"brand": "Strack & Van Til", "brand_wikidata": "Q17108969"}
    start_urls = ["https://www.strackandvantil.com/wp-content/themes/svt/svt-ajax.php?action=get_locations"]

    def pre_process_data(self, feature: dict) -> None:
        feature.pop("email", None)
        feature.pop("webUrl", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["uniqueName"]
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("street", None)
        item["opening_hours"] = OpeningHours()
        for rule in feature.get("operatingHours") or []:
            item["opening_hours"].add_ranges_from_string(f"{rule['day']}: {rule['hours']}")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
