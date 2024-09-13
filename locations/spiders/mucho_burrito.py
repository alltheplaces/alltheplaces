from locations.storefinders.where2getit import Where2GetItSpider


class MuchoBurritoSpider(Where2GetItSpider):
    name = "mucho_burrito"
    item_attributes = {
        "brand_wikidata": "Q65148332",
        "brand": "Mucho Burrito",
    }
    api_key = "F18F9C0C-3871-11EE-9ED6-49504A66C4B2"
