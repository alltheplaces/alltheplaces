from urllib.parse import urljoin

from locations.json_blob_spider import JSONBlobSpider


class EnglishHeritageGBSpider(JSONBlobSpider):
    name = "english_heritage_gb"
    item_attributes = {"brand": "English Heritage", "brand_wikidata": "Q936287"}
    start_urls = ["https://www.english-heritage.org.uk/api/PropertySearch/GetAll"]
    no_refs = True
    locations_key = "Results"


def post_process_item(self, item, response, location):
    item["website"] = urljoin("https://stores.sainsburys.co.uk/{}/{}", location["Path"])
    yield item
