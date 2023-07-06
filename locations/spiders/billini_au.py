from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class BilliniAUSpider(StockistSpider):
    name = "billini_au"
    item_attributes = {"brand": "Billini", "brand_wikidata": "Q117747826"}
    key = "u5133"
