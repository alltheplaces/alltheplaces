import re

from unidecode import unidecode

from locations.storefinders.woosmap import WoosmapSpider


class DecathlonFRSpider(WoosmapSpider):
    name = "decathlon_fr"
    item_attributes = {"brand": "Decathlon", "brand_wikidata": "Q509349"}
    key = "woos-c7283e70-7b4b-3c7d-bbfe-e65958b8769b"
    origin = "https://www.decathlon.fr"
    website_template = "https://www.decathlon.fr/store-view/magasin-de-sports-{slug}-{ref}"

    def parse_item(self, item, feature):
        slug = re.sub(r"[^\w]+", " ", unidecode(item["name"].lower()).strip()).replace(" ", "-")
        item["website"] = self.website_template.format(slug=slug, ref=item["ref"])
        props = feature["properties"]["user_properties"]
        publish_on_website = props["publishOnEcommerce"]
        if publish_on_website:
            yield item
