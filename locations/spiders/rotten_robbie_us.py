from locations.categories import Categories
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class RottenRobbieUSSpider(WpGoMapsSpider):
    name = "rotten_robbie_us"
    item_attributes = {"brand": "Rotten Robbie", "brand_wikidata": "Q87378070", "extras": Categories.FUEL_STATION.value}
    start_urls = [
        "https://www.rottenrobbie.com/wp-json/wpgmza/v1/features/base64eJyrVkrLzClJLVKyUqqOUcpNLIjPTIlRsopRMoxRqlWqBQCnUQoG"
    ]
