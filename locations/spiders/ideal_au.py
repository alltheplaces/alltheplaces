from locations.storefinders.rexel import RexelSpider


class IdealAUSpider(RexelSpider):
    name = "ideal_au"
    item_attributes = {"brand": "Ideal Electrical (Australia)", "brand_wikidata": "Q"}
    base_url = "www.idealelectrical.com/aie"
    search_lat = -33
    search_lon = 151

    def parse_item(self, item, feature, **kwargs):
        yield item
