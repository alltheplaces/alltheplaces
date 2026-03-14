from locations.categories import Categories
from locations.storefinders.stat import StatSpider


class TheHalalGuysSpider(StatSpider):
    name = "the_halal_guys"
    item_attributes = {"brand": "The Halal Guys", "brand_wikidata": "Q10846129", "extras": Categories.FAST_FOOD.value}
    start_urls = ["https://thehalalguys.com/stat/api/locations/search?limit=20000"]
