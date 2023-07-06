from locations.storefinders.uberall import UberallSpider


class AldiNordLUSpider(UberallSpider):
    name = "aldi_nord_lu"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373"}
    key = "ALDINORDLU_klnge16WJnsW3DwfI5HVH28kqvo9sp"

    def parse_item(self, item, feature, **kwargs):
        item["ref"] = str(feature["id"])
        slug = "/".join([item["city"], item["street_address"], item["ref"]]).lower().replace(" ", "-")
        item["website"] = "https://www.aldi.lu/de/information/supermaerkte.html/l/" + slug
        yield item
