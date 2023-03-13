from locations.storefinders.where2getit import Where2GetItSpider


class TheCheesecakeFactorySpider(Where2GetItSpider):
    name = "thecheesecakefactory"
    item_attributes = {"brand": "The Cheesecake Factory", "brand_wikidata": "Q1045842"}
    w2gi_id = "320C479E-6D70-11DE-9D8B-E57E37ABAA09"
    w2gi_filter = {
        "or": {
            "CATERINGFLAG": {"EQ": ""},
            "CURBSIDEFLAG": {"EQ": ""},
            "DELIVERYFLAG": {"EQ": ""},
            "BANQUETS": {"eq": ""},
            "PATIO": {"eq": ""},
        }
    }
    w2gi_query = "CA"
