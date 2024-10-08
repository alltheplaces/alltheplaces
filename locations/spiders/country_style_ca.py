from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class CountryStyleCASpider(SuperStoreFinderSpider):
    name = "country_style_ca"
    item_attributes = {
        "brand_wikidata": "Q5177435",
        "brand": "Country Style",
    }
    allowed_domains = [
        "locations.countrystyle.com",
    ]
