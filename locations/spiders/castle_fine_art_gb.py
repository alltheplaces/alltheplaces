from locations.categories import Categories, apply_category
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.stockist import StockistSpider


class CastleFineArtGBSpider(StockistSpider):
    name = "castle_fine_art_gb"
    item_attributes = {"brand": "Castle Fine Art", "brand_wikidata": "Q136092887"}
    key = "map_p3x4ry63"

    def parse_item(self, item, location):
        item["branch"] = item.pop("name")
        item["name"] = "Castle Fine Art"
        item["street_address"] = merge_address_lines([location["address_line_1"], location["address_line_2"]])
        item.pop("facebook", None)
        item.pop("twitter", None)
        apply_category(Categories.SHOP_ART, item)
        yield item
