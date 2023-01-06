from locations.spiders.mcdonalds import McDonaldsSpider
from locations.storefinders.woosmap import WoosmapSpider


class McDonaldsFRSpider(WoosmapSpider):
    name = "mcdonalds_fr"
    item_attributes = McDonaldsSpider.item_attributes
    key = "woos-77bec2e5-8f40-35ba-b483-67df0d5401be"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Origin": "https://www.mcdonalds.fr"}}

    def parse_item(self, item, feature, **kwargs):
        item[
            "website"
        ] = f'https://www.mcdonalds.fr/restaurants{feature["properties"]["contact"]["website"]}/{feature["properties"]["store_id"]}'
        yield item
