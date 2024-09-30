from locations.categories import Categories
from locations.storefinders.storemapper import StoremapperSpider


class ToysRUSGBSpider(StoremapperSpider):
    name = "toys_r_us_gb"
    item_attributes = {"brand": "Toys R Us UK", "brand_wikidata": "Q125186363", "located_in": "WHSmith", "located_in:wikidata": "Q1548712", "extras": Categories.SHOP_TOYS.value}
    company_id: str = "26714-C1AzPSOgcoRLNRqU"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_item(self, item, location):
        yield item
