from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.algolia import AlgoliaSpider


class BlueBottleCoffeeSpider(AlgoliaSpider):
    name = "blue_bottle_coffee"
    item_attributes = {"brand": "Blue Bottle Coffee", "brand_wikidata": "Q4928917"}
    api_key = "d5c811630429fa52f432899fe1935c9f"
    app_id = "1WJCUS8NHR"
    index_name = "us-production-cafes"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        del item["name"]
        del item["street"]

        slug = feature["slug"]["current"]

        item["branch"] = feature["name"]["eng"]
        item["image"] = feature.get("image", {}).get("source", {}).get("secure_url")
        item["ref"] = slug
        item["state"] = feature["address"]["district"]
        item["street_address"] = merge_address_lines([feature["address"]["street"], feature["address"].get("extended")])
        item["website"] = f"https://bluebottlecoffee.com/us/eng/cafes/{slug}"

        yield item
