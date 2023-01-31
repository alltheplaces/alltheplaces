from locations.storefinders.rexel import RexelSpider


class RexelDESpider(RexelSpider):
    name = "rexel_de"
    item_attributes = {"brand": "Rexel (Germany)", "brand_wikidata": "Q"}
    base_url = "www.rexel.de"
    search_lat = 50
    search_lon = 11

    def parse_item(self, item, feature, **kwargs):
        yield item
