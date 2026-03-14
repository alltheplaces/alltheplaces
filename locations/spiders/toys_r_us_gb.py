from locations.categories import Categories, apply_category
from locations.storefinders.storemapper import StoremapperSpider


class ToysRUSGBSpider(StoremapperSpider):
    name = "toys_r_us_gb"
    item_attributes = {
        "brand": "Toys R Us",
        "brand_wikidata": "Q125186363",
        "located_in": "WHSmith",
        "located_in_wikidata": "Q1548712",
    }
    company_id: str = "26714-C1AzPSOgcoRLNRqU"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_item(self, item, location):
        apply_category(Categories.SHOP_TOYS, item)
        yield item
