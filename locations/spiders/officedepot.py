from locations.storefinders.where2getit import Where2GetItSpider


class OfficeDepotSpider(Where2GetItSpider):
    name = "office_depot"
    item_attributes = {
        "brand_wikidata": "Q1337797",
        "brand": "Office Depot",
    }
    api_key = "592778B0-A13B-11EB-B3DB-84030D516365"