import html

from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BarBurritoCASpider(WPStoreLocatorSpider):
    name = "bar_burrito_ca"
    item_attributes = {"brand": "BarBurrito", "brand_wikidata": "Q104844862"}
    allowed_domains = ["www.barburrito.ca"]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["branch"] = html.unescape(item.pop("name"))
        del item["addr_full"]

        yield item

    def parse_opening_hours(self, location: dict, **kwargs):
        # TODO: php serialized format
        return None
