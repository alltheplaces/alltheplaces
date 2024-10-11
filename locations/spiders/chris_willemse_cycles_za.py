from locations.categories import Categories, apply_category
from locations.spiders.cycle_lab_za import CycleLabZASpider


class ChrisWillemseCyclesZASpider(CycleLabZASpider):
    name = "chris_willemse_cycles_za"
    item_attributes = {"brand": "Chris Willemse Cycles", "brand_wikidata": "Q130488816"}
    start_urls = ["https://cwcycles.co.za/store-location"]

    def post_process_item(self, item, response, location):
        item["name"] = item.pop("branch")
        apply_category(Categories.SHOP_BICYCLE, item)
        yield item
