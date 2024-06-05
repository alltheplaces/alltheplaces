from locations.categories import Categories
from locations.storefinders.yext_answers import YextAnswersSpider


class PrimantiBrosUSSpider(YextAnswersSpider):
    name = "primanti_bros_us"
    item_attributes = {"brand": "Primanti Bros", "brand_wikidata": "Q7243049", "extras": Categories.RESTAURANT.value}
    api_key = "7515c25fc685bbdd7c5975b6573c6912"
    experience_key = "locator"

    def parse_item(self, location, item):
        item["website"] = location["data"].get("landingPageUrl")
        yield item
