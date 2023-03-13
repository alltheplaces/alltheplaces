from locations.storefinders.where2getit import Where2GetItSpider


class TraderJoesSpider(Where2GetItSpider):
    name = "trader_joes"
    item_attributes = {"brand": "Trader Joe's", "brand_wikidata": "Q688825"}
    w2gi_id = "8559C922-54E3-11E7-8321-40B4F48ECC77"
    w2gi_query = "CA"
    w2gi_filter = {"or": {"wine": {"eq": ""}, "beer": {"eq": ""}, "liquor": {"eq": ""}, "comingsoon": {"eq": ""}}}
