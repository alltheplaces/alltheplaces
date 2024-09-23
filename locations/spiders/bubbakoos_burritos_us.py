from locations.storefinders.where2getit import Where2GetItSpider


class BubbakoosBurritosUSSpider(Where2GetItSpider):
    name = "bubbakoos_burritos_us"
    item_attributes = {
        "brand_wikidata": "Q114619751",
        "brand": "Bubbakoo's Burritos",
    }
    api_endpoint = "https://locations.bubbakoos.com/rest/getlist"
    api_key = "DAD82608-FE61-11EE-B900-E7D4C42605F6"
