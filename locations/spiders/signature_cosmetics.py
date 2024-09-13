import chompjs

from locations.json_blob_spider import JSONBlobSpider


class SignatureCosmeticsSpider(JSONBlobSpider):
    name = "signature_cosmetics"
    item_attributes = {
        "brand": "Signature Cosmetics & Fragrances",
        "brand_wikidata": "Q116894514",
    }
    start_urls = ["https://www.signaturecosmetics.co.za/store-locator"]

    def extract_json(self, response):
        data_raw = response.xpath("//script[contains(text(), 'SEARCHORGUNITLOCATIONS')]/text()").get()
        data_raw = data_raw.split("SEARCHORGUNITLOCATIONS", 1)[1]
        return chompjs.parse_js_object(data_raw)["SEARCHORGUNITLOCATIONS"]["item"]["result"]

    def post_process_item(self, item, response, location):
        item["ref"] = location.get("OrgUnitNumber")
        item.pop("street")
        item["branch"] = location.get("OrgUnitName")
        item["phone"] = "; ".join(
            [contact["Locator"] for contact in location["Contacts"] if contact["ContactTypeValue"] == 1]
        )
        item["email"] = "; ".join(
            [contact["Locator"] for contact in location["Contacts"] if contact["ContactTypeValue"] == 2]
        )
        if item["state"] is not None:
            try:
                int(item["state"])
                item.pop("state")
            except ValueError:
                pass
        yield item
