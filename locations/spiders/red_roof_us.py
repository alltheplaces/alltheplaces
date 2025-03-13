import re

from scrapy.http import JsonRequest

from locations.json_blob_spider import JSONBlobSpider


BRANDS = {
    "RRI": {"brand": "Red Roof Inn", "brand_wikidata": "Q7304949"},
    "RRIPLUS": {"brand": "Red Roof PLUS+"},
    "REDCOLLECT": {"brand": "Red Collection"},
    "HTS": {"brand": "HomeTowne Studios", "brand_wikidata": "Q109868848"},
}

def slugify(s):
    return re.sub(r"\s+", "-", s).lower()

class RedRoofUSSpider(JSONBlobSpider):
    name = "red_roof_us"
    item_attributes = {
        "brand_wikidata": "Q7304949",
    }
    
    def start_requests(self):
        yield JsonRequest("https://prd-redroofwebapi.redroof.com/api/v1/Property/get-all-properties", data=list(BRANDS.keys()))

    def post_process_item(self, item, response, location):
        item.update(BRANDS[location["brand"]])
        item["ref"] = location["PropertyCode"]
        item["name"] = location["description"]
        item["street_address"] = location["street1"]
        item["extras"]["fax"] = location["faxNumber"]
        item["website"] = f"https://www.redroof.com/property/{slugify(location['state'])}/{slugify(location['city'])}/{slugify(location['PropertyCode'])}"
        if location["propertyName"] != location["description"]:
            item["branch"] = location["propertyName"]
        yield item
