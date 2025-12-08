from locations.storefinders.where2getit import Where2GetItSpider


class NekterJuiceBarUSSpider(Where2GetItSpider):
    name = "nekter_juice_bar_us"
    item_attributes = {
        "brand_wikidata": "Q112826281",
        "brand": "Nékter Juice Bar",
    }
    api_endpoint = "https://locations.nekterjuicebar.com/rest/getlist"
    api_key = "1B5DBC6C-2A2B-11EE-843A-8413326043C3"
