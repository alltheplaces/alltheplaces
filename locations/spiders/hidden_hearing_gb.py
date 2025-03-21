from locations.json_blob_spider import JSONBlobSpider


class HiddenHearingGBSpider(JSONBlobSpider):
    name = "hidden_hearing_gb"
    item_attributes = {"brand": "Hidden Hearing", "brand_wikidata": "Q107301478"}
    start_urls = ["https://www.hiddenhearing.co.uk/api/clinics/getclinics/%7B22907258-EC4D-4701-BC3C-9F0A3A3204F9%7D"]

    def post_process_item(self, item, response, location):
        item["website"] = "https://www.hiddenhearing.co.uk" + item["website"]
        if item["phone"] == "0800 740 8706":
            item.pop("phone")
        if item["email"] == "info@hiddenhearing.co.uk ":
            item.pop("email")
        yield item
