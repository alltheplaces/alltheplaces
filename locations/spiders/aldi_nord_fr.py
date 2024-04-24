from locations.storefinders.uberall import UberallSpider


class AldiNordFRSpider(UberallSpider):
    name = "aldi_nord_fr"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373"}
    key = "ALDINORDFR_Mmljd17th8w26DMwOy4pScWk4lCvj5"

    def parse_item(self, item, feature, **kwargs):
        item["branch"] = item.pop("name").removeprefix("ALDI ")

        yield item
