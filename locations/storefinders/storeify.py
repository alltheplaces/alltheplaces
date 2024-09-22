import chompjs
from scrapy import Request

from locations.dict_parser import DictParser
from locations.json_blob_spider import JSONBlobSpider


class StoreifySpider(JSONBlobSpider):
    """
    Storeify is a shopify related storefinder.

    Detectable via `https://sl.storeify.app/js/stores/{api_key}/storeifyapps-storelocator-geojson.js`

    To use, specify `api_key` and `domain`
    """

    api_key = None
    domain = None

    # TODO: Autodetection

    def start_requests(self):
        yield Request(url=f"https://sl.storeify.app/js/stores/{self.api_key}/storeifyapps-storelocator-geojson.js")

    # API returns a geojson feature collection
    def extract_json(self, response):
        return chompjs.parse_js_object(response.text)["features"]

    def parse_feature_array(self, response, feature_array):
        for feature in feature_array:
            self.pre_process_data(feature)
            item = DictParser.parse(feature["properties"])

            item["image"] = feature["properties"]["thumbnail"]
            item["url"] = self.domain + item["url"]

            # TODO: Parse hours
            # "schedule": "<div class=\"title-store-info\">{{ store_operation }}</div><div class=\"content-store-info\"><table class=\"work-time table\"><tr class=\"row-mon\"><th class=\"dayname\">{{ mon }}</th><td>09:00 {{ am }} - 06:00 {{ pm }}</td></tr><tr class=\"row-tue\"><th class=\"dayname\">{{ tue }}</th><td>09:00 {{ am }} - 06:00 {{ pm }}</td></tr><tr class=\"row-wed\"><th class=\"dayname\">{{ wed }}</th><td>09:00 {{ am }} - 06:00 {{ pm }}</td></tr><tr class=\"row-thu\"><th class=\"dayname\">{{ thu }}</th><td>09:00 {{ am }} - 06:00 {{ pm }}</td></tr><tr class=\"row-fri\"><th class=\"dayname\">{{ fri }}</th><td>09:00 {{ am }} - 06:00 {{ pm }}</td></tr><tr class=\"row-sat\"><th class=\"dayname\">{{ sat }}</th><td>09:00 {{ am }} - 03:00 {{ pm }}</td></tr><tr class=\"row-sun\"><th class=\"dayname\">{{ sun }}</th><td>{{ closed }}</td></tr></table></div>",

            yield from self.post_process_item(item, response, feature) or []
