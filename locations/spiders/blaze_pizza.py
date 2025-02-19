from locations.storefinders.nomnom import NomNomSpider, slugify


class BlazePizzaSpider(NomNomSpider):
    name = "blaze_pizza"
    item_attributes = {"brand": "Blaze Pizza", "brand_wikidata": "Q23016666"}
    start_urls = ["https://nomnom-prod-api.blazepizza.com/extras/restaurant/summary/state"]

    def post_process_item(self, item, response, feature):
        item["extras"]["website:menu"] = feature["url"]
        street_address = feature["streetaddress"]
        street_address_no_unit = street_address[: street_address.find(",")] if "," in street_address else street_address
        item["website"] = (
            f"https://locations.blazepizza.com/{slugify(feature['state'])}/{slugify(feature['city'])}/{slugify(street_address_no_unit)}"
        )
        yield item
