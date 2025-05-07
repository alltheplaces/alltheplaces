from scrapy.http import JsonRequest

from locations.storefinders.stockist import StockistSpider


class TheBodyShopAUCASpider(StockistSpider):
    name = "the_body_shop_au_ca"
    item_attributes = {"brand": "The Body Shop", "brand_wikidata": "Q837851"}
    keys = ["map_g3y2xkzq", "map_r325r4wq"]

    def start_requests(self):
        for key in self.keys:
            yield JsonRequest(
                url=f"https://stockist.co/api/v1/{key}/locations/all",
                callback=self.parse_all_locations,
                errback=self.parse_all_locations_error,
            )
