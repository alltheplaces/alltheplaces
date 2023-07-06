from locations.storefinders.uberall import UberallSpider


class AldiNordBESpider(UberallSpider):
    name = "aldi_nord_be"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373"}
    key = "ALDINORDBE_4QRaIWlJgn529tNr9oXuh0fFhxYo9V"

    def parse_item(self, item, feature, **kwargs):
        item["ref"] = str(feature["id"])
        slug = "/".join([item["city"], item["street_address"], item["ref"]]).lower().replace(" ", "-")
        item["website"] = "https://www.aldi.be/nl/informatie/supermarkten.html/l/" + slug
        yield item
