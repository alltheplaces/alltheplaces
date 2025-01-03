from urllib.parse import urljoin

from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class EnglishHeritageGBSpider(JSONBlobSpider):
    name = "english_heritage_gb"
    item_attributes = {"brand": "English Heritage", "brand_wikidata": "Q936287"}
    start_urls = ["https://www.english-heritage.org.uk/api/PropertySearch/GetAll"]
    no_refs = True
    locations_key = "Results"
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "user-agent": BROWSER_DEFAULT,
        },
    }

    def post_process_item(self, item, response, location):
        item["website"] = urljoin("https://www.english-heritage.org.uk", location["Path"])
        yield item
