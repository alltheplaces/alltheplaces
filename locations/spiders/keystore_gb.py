import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KeystoreGBSpider(JSONBlobSpider):
    name = "keystore_gb"
    item_attributes = {"brand": "KeyStore", "brand_wikidata": "Q50528754"}
    start_urls = ["https://www.keystore.co.uk/wp-admin/admin-ajax.php?action=get_all_stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = feature["gu"]
        item["phone"] = feature.get("te")
        item["street_address"] = feature["st"]
        item["postcode"] = feature["zp"]
        item["city"] = feature["ct"].strip()
        item["country"] = feature["co"].strip()

        if "KeyStoreExpress-MapPin" in feature["ic"]:
            item["name"] = "KeyStore Express"
        elif "KeyStoreMore-MapPin" in feature["ic"]:
            item["name"] = "KeyStore More"
        elif "KeyStore-MapPin" in feature["ic"]:
            item["name"] = "KeyStore"
        else:
            self.logger.warning("Unknown store type: {}".format(feature["ic"]))
            self.crawler.stats.inc_value("{}/unknown_store_type/{}".format(self.name, feature["ic"]))

        item["branch"] = re.sub(item["name"], "", feature["na"], flags=re.IGNORECASE).strip()

        features = feature["fi"].values()
        apply_yes_no(Extras.ATM, item, "ATM" in features)
        apply_yes_no(PaymentMethods.CONTACTLESS, item, "Contactless" in features)
        apply_yes_no("sells:lottery", item, "Lottery" in features)
        apply_yes_no("sells:alcohol", item, "Off Licence" in features)
        apply_yes_no("paypoint", item, "Paypoint" in features)

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
