from locations.categories import Categories
from locations.storefinders.woosmap import WoosmapSpider


class MbplcGBSpider(WoosmapSpider):
    name = "mbplc_gb"
    key = "woos-19f74f73-0b20-3571-b9ef-706ad3dbad27"
    origin = "https://www.mbplc.com/"

    brand_mapping = {
        "Sizzling Pubs": {"brand": "Sizzling Pubs", "brand_wikidata": "Q118314187"},
        "All Bar One": {"brand": "All Bar One", "brand_wikidata": "Q4728624"},
        "Browns Restaurants": {"brand": "Browns Restaurants", "brand_wikidata": "Q4976672"},
        "Ember Inns": {"brand": "Ember Inns", "brand_wikidata": "Q116272278"},
        "Harvester": {"brand": "Harvester", "brand_wikidata": "Q5676915"},
        "Miller & Carter": {"brand": "Miller & Carter", "brand_wikidata": "Q87067401"},
        "Nicholsons": {"brand": "Nicholsons", "brand_wikidata": "Q113130666"},
        "O'Neill's": {"brand": "O'Neill's", "brand_wikidata": "Q7071905"},
        "Premium Country Pubs": {
            "brand": "Premium Country Pubs",
            "brand_wikidata": "Q118606900",
            "extras": Categories.PUB.value,
        },
        "Stonehouse": {"brand": "Stonehouse", "brand_wikidata": "Q78192049"},
        "Toby Carvery": {"brand": "Toby Carvery", "brand_wikidata": "Q7811777"},
        "Oak Tree pubs": {
            "brand": "Oak Tree pubs",
            "brand_wikidata": "",
            "extras": Categories.PUB.value,
        },
        "Inn Keepers Collection": {
            "brand": "Inn Keepers Collection",
            "brand_wikidata": "",
            "extras": Categories.PUB.value,
        },
        "Vintage Inns": {"brand": "Vintage Inns", "brand_wikidata": "Q87067899"},
        "Browns": {"brand": "Browns", "brand_wikidata": "Q4976672"},
        "Son of Steak": {
            "brand": "Son of Steak",
            "brand_wikidata": "",
            "extras": Categories.PUB.value,
        },
        "Neighbourhood Pubs": {
            "brand": "Neighbourhood Pubs",
            "brand_wikidata": "",
            "extras": Categories.PUB.value,
        },
        "Castle": {
            "brand": "Castle",
            "brand_wikidata": "",
            "extras": Categories.PUB.value,
        },
    }

    def parse_item(self, item, feature, **kwargs):
        if match := self.brand_mapping.get(feature["properties"]["user_properties"]["brand"]):
            item.update(match)
        item["website"] = feature["properties"]["user_properties"]["websiteUrl"]

        yield item
