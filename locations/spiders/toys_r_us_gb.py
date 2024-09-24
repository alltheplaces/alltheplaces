from locations.categories import Categories
from locations.storefinders.storemapper import StoremapperSpider


class ToysRUSGBSpider(StoremapperSpider):
    name = "toys_r_us_gb"
    item_attributes = {"brand": "Toys R Us UK", "brand_wikidata": "Q125186363", "extras": Categories.SHOP_TOYS.value}
    company_id: str = "26714-C1AzPSOgcoRLNRqU"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_item(self, item, location):
        yield item
