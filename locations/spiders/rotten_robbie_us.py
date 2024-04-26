from locations.categories import Categories
from locations.storefinders.wp_go_maps import WPGoMapsSpider


class RottenRobbieUSSpider(WPGoMapsSpider):
    name = "rotten_robbie_us"
    item_attributes = {"brand": "Rotten Robbie", "brand_wikidata": "Q87378070", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["www.rottenrobbie.com"]
