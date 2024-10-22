import chompjs
from scrapy.http import Response

from locations.json_blob_spider import JSONBlobSpider


class LeeannChinUSSpider(JSONBlobSpider):
    name = "leeann_chin_us"
    item_attributes = {
        "brand": "Leeann Chin",
        "brand_wikidata": "Q6515716",
    }
    start_urls = ["https://www.leeannchin.com/locations"]

    def extract_json(self, response: Response) -> list:
        return chompjs.parse_js_object(response.xpath('//script[contains(text(), "var jsonContent")]/text()').get())[
            "data"
        ]
