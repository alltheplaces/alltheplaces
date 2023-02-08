from locations.items import Feature
from locations.storefinders.storerocket import StorerocketSpider


class FastbreakUSSpider(StorerocketSpider):
    name = "fastbreak_us"
    item_attributes = {"brand": "Fastbreak", "brand_wikidata": "Q116731804"}
    storerocket_id = "WwzpABj4dD"

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["website"] = f'https://www.myfastbreak.com/locations?location={location["slug"]}'

        yield item
