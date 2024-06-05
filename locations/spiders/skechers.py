from locations.storefinders.where2getit import Where2GetItSpider


class SkechersSpider(Where2GetItSpider):
    name = "skechers"
    item_attributes = {
        "brand_wikidata": "Q2945643",
        "brand": "Skechers",
    }
    allowed_domains = [
        "local.skechers.com",
    ]
    api_key = "8C3F989C-6D95-11E1-9DE0-BB3690553863"
