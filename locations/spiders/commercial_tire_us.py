from locations.storefinders.storerocket import StoreRocketSpider


class CommercialTireUSSpider(StoreRocketSpider):
    name = "commercial_tire_us"
    item_attributes = {"brand": "Commercial Tire", "brand_wikidata": "Q28403810"}
    storerocket_id = "BZJWPVY80o"
