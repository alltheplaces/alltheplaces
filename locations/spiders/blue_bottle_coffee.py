from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.algolia import AlgoliaSpider


class BlueBottleCoffeeSpider(AlgoliaSpider):
    name = "blue_bottle_coffee"
    item_attributes = {"brand": "Blue Bottle Coffee", "brand_wikidata": "Q4928917"}
    api_key = "d5c811630429fa52f432899fe1935c9f"
    app_id = "1WJCUS8NHR"
    index_name = "us-production-cafes"

    def post_process_item(self, item, response, location):
        del item["name"]
        del item["street"]

        slug = location["slug"]["current"]

        item["branch"] = location["name"]["eng"]
        item["image"] = location.get("image", {}).get("source", {}).get("secure_url")
        item["ref"] = slug
        item["state"] = location["address"]["district"]
        item["street_address"] = merge_address_lines(
            [location["address"]["street"], location["address"].get("extended")]
        )
        item["website"] = f"https://bluebottlecoffee.com/us/eng/cafes/{slug}"

        yield item
