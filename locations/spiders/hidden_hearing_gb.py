from locations.json_blob_spider import JSONBlobSpider


class HiddenHearingGBSpider(JSONBlobSpider):
    name = "hidden_hearing_gb"
    item_attributes = {"brand": "Hidden Hearing", "brand_wikidata": "Q107301478"}
    start_urls = ["https://www.hiddenhearing.co.uk/api/clinics/getclinics/%7B22907258-EC4D-4701-BC3C-9F0A3A3204F9%7D"]
