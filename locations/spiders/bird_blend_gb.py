from locations.storefinders.stockist import StockistSpider


class BirdBlendGBSpider(StockistSpider):
    name = "bird_blend_gb"
    item_attributes = {"brand": "Bird & Blend Tea Co", "brand_wikidata": "Q116985265"}
    key = "map_9q94xv43"
