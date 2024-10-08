from locations.storefinders.where2getit import Where2GetItSpider


class WabaGrillUSSpider(Where2GetItSpider):
    name = "waba_grill_us"
    item_attributes = {
        "brand_wikidata": "Q113163467",
        "brand": "WaBa Grill",
    }
    api_endpoint = "https://locations.wabagrill.com/rest/getlist"
    api_key = "7512DE42-E61C-11EE-B773-E61A326043C3"
