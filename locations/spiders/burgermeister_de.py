from locations.storefinders.wp_go_maps import WpGoMapsSpider
from locations.user_agents import BROWSER_DEFAULT


class BurgermeisterDESpider(WpGoMapsSpider):
    name = "burgermeister_de"
    item_attributes = {"brand": "Burgermeister", "brand_wikidata": "Q116382535"}
    start_urls = ["https://burgermeister.com/api-json.php?filter=%7B%22map_id%22%3A%226%22%2C%22mashupIDs%22%3A%5B%5D%2C%22customFields%22%3A%5B%5D%7D&route=%2Ffeatures%2F&action=wpgmza_rest_api_request"]
    allowed_domains = ["burgermeister.com"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item, location):
        item["image"] = location.get("pic")
        item["branch"] = item.pop("name")

        yield item