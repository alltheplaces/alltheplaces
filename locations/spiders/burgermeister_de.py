from locations.storefinders.wp_go_maps import WpGoMapsSpider
from locations.user_agents import BROWSER_DEFAULT


class BurgermeisterDESpider(WpGoMapsSpider):
    name = "burgermeister_de"
    item_attributes = {"brand": "Burgermeister", "brand_wikidata": "Q116382535"}
    allowed_domains = ["burgermeister.com"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
