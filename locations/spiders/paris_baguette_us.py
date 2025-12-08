import re

from locations.storefinders.stat import StatSpider


class ParisBaguetteUSSpider(StatSpider):
    name = "paris_baguette_us"
    item_attributes = {"brand": "Paris Baguette", "brand_wikidata": "Q62605260"}
    start_urls = ["https://parisbaguette.com/stat/api/locations/search?limit=20000&fields=displayname_displaynameline1"]

    def post_process_item(self, item, response, store):
        match = re.search(r"\((\d+)\)", item["ref"])
        if match:
            item["ref"] = match.group(1)
        item["branch"] = store["displayFields"]["displayname_displaynameline1"]
        yield item
