from locations.storefinders.where2getit import Where2GetItSpider


class NekterJuiceBarUSSpider(Where2GetItSpider):
    name = "nekter_juice_bar_us"
    item_attributes = {
        "brand_wikidata": "Q112826281",
        "brand": "Nékter Juice Bar",
    }
    api_brand_name = "nektersites"
    api_key = "AF0813FE-43DA-11EE-B2BD-FA7C2CD69500"
