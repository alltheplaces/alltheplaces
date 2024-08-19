from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class GoGamesToysUSSpider(WPStoreLocatorSpider):
    name = "go_games_toys_us"
    item_attributes = {
        "brand_wikidata": "Q108312837",
        "brand": "Go! Games & Toys",
    }
    allowed_domains = [
        "goretailgroup.com",
    ]
    max_results = 100
    iseadgg_countries_list = ["US"]
    # https://goretailgroup.com/wp-admin/admin-ajax.php?action=store_search&lat=29.42519&lng=-98.49459&max_results=100&search_radius=500
    # Max is 500 miles
    search_radius = 500
    days = DAYS_EN

    def parse_item(self, item, location):
        if item["name"] == "Attic Salt":
            item["brand"] = "Attic Salt"
            item["brand_wikidata"] = "Q108409773"

        # "name" field contains:
        #   - "Attic Salt"
        #   - "Go! Games & Toys"
        #   - "Go! Calendars Games & Toys"
        #   - "Go! Calendars, Games and Toys"
        #   - "Go!CalendarsGamesToys&Books"
        #   - etc
        # Due to the inconsistencies, we'll just drop the field completely
        # so that the "brand" value is used instead. There is no branch name
        # to extract from the "name" field.
        item.pop("name", None)

        yield item
