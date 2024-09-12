import re

from locations.categories import Categories
from locations.storefinders.stat import StatSpider


class ParisBaguetteCASpider(StatSpider):
    name = "paris_baguette_ca"
    item_attributes = {"brand": "Paris Baguette", "brand_wikidata": "Q62605260", "extras": Categories.SHOP_BAKERY.value}
    start_urls = ["https://parisbaguette.ca/stat/api/locations/search?limit=20000&fields=displayname_displaynameline1"]

    def post_process_item(self, item, response, store):
        item["ref"] = re.search(r"\((\d+C)\)", item["ref"]).group(1)
        item["branch"] = store["displayFields"]["displayname_displaynameline1"]
        yield item
