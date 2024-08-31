from locations.storefinders.rio_seo import RioSeoSpider


class TrulyNolenUSSpider(RioSeoSpider):
    name = "truly_nolen_us"
    item_attributes = {
        "brand_wikidata": "Q7847671",
        "brand": "Truly Nolen",
    }
    end_point = "https://maps.locations.trulynolen.com"
