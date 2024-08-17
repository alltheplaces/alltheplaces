from locations.storefinders.uberall import UberallSpider


class JustOverTheTopSpider(UberallSpider):
    name = "just_over_the_top"
    item_attributes = {
        "brand_wikidata": "Q104890420",
        "brand": "Just Over the Top",
    }
    key = "GebVCV1XBZBklJ6rQ5N2y44PCNLOpB"
