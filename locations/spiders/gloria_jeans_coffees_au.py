import html

from scrapy.http import JsonRequest

from locations.geo import city_locations
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class GloriaJeansCoffeesAUSpider(WPStoreLocatorSpider):
    name = "gloria_jeans_coffees_au"
    item_attributes = {"brand": "Gloria Jean's Coffees", "brand_wikidata": "Q2666365"}
    time_format = "%I:%M %p"

    def start_requests(self):
        for city in city_locations("AU", 100000):
            yield JsonRequest(
                url=f'https://www.gloriajeanscoffees.com.au/wp/wp-admin/admin-ajax.php?action=store_search&lat={city["latitude"]}&lng={city["longitude"]}&autoload=1'
            )

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["name"] = html.unescape(location["store"])
        yield item
