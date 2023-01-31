from locations.storefinders.rexel import RexelSpider


class RexelGBSpider(RexelSpider):
    name = "denmans_gb"
    item_attributes = {"brand": "Rexel", "brand_wikidata": "Q"}
    base_url = "www.rexel.co.uk/uki"
    search_lat = 51
    search_lon = -0

    def parse_item(self, item, feature, **kwargs):
        yield item
