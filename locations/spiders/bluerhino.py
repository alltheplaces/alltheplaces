import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BlueRhinoSpider(scrapy.Spider):
    name = "bluerhino"
    item_attributes = {
        "brand": "Blue Rhino",
        "brand_wikidata": "Q65681213",
        "country": "US",
    }
    allowed_domains = ["bluerhino.com"]
    start_urls = [
        "https://bluerhino.com/api/propane/GetRetailersNearPoint?latitude=0&longitude=0&radius=10000&name=&type=&top=500000&cache=false"
    ]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept": "application/json"}}

    def parse(self, response):
        for row in response.json():
            properties = {
                "lat": row["Latitude"],
                "lon": row["Longitude"],
                "ref": row["RetailKey"],
                "located_in": row["RetailName"],
                "street_address": merge_address_lines([row["Address1"], row["Address2"], row["Address3"]]),
                "city": row["City"],
                "state": row["State"],
                "postcode": row["Zip"],
                "country": row["Country"],
                "phone": row["Phone"],
                "extras": {"fax": row["Fax"], "check_date": row["LastDeliveryDate"].split("T", 1)[0]},
            }
            yield Feature(**properties)
