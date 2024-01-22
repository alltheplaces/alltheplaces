from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class TheExerciseCoachUSSpider(AgileStoreLocatorSpider):
    name = "the_exercise_coach_us"
    item_attributes = {
        "brand": "The Exercise Coach",
        "brand_wikidata": "Q121502262",
        "extras": Categories.GYM.value,
    }
    allowed_domains = ["exercisecoach.com"]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["branch"] = item.pop("name")
        yield item
