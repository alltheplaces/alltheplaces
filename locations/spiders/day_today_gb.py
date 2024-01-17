import html

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DayTodayGBSpider(WPStoreLocatorSpider):
    name = "day_today_gb"
    item_attributes = {"brand": "Day-Today", "brand_wikidata": "Q121435331"}
    allowed_domains = ["www.day-today.co.uk"]
    time_format = "%I:%M %p"

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["name"] = html.unescape(item["name"])
        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
