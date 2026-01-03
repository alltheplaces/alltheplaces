from typing import AsyncIterator, Iterable

from chompjs import parse_js_object
from scrapy.http import Request, TextResponse

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class StoreifySpider(JSONBlobSpider):
    """
    Storeify is a shopify related storefinder.

    Detectable via `https://sl.storeify.app/js/stores/{api_key}/storeifyapps-storelocator-geojson.js`

    To use, specify `api_key` and `domain`, where `domain` is the domain used
    for individual store/feature webpages at the brand's website (e.g.
    "stores.example.net/stores/example-location").
    """

    dataset_attributes: dict = {"source": "api", "api": "storeify.app"}
    api_key: str
    domain: str

    # TODO: Autodetection

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url=f"https://sl.storeify.app/js/stores/{self.api_key}/storeifyapps-storelocator-geojson.js")

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        # API returns a GeoJSON feature collection
        return parse_js_object(response.text)["features"]

    def parse_feature_array(self, response: TextResponse, feature_array: list) -> Iterable[Feature]:
        for feature in feature_array:
            self.pre_process_data(feature)
            item = DictParser.parse(feature["properties"])

            item["image"] = feature["properties"]["thumbnail"]
            item["website"] = self.domain + item["website"]

            # TODO: Parse hours
            # "schedule": "<div class=\"title-store-info\">{{ store_operation }}</div><div class=\"content-store-info\"><table class=\"work-time table\"><tr class=\"row-mon\"><th class=\"dayname\">{{ mon }}</th><td>09:00 {{ am }} - 06:00 {{ pm }}</td></tr><tr class=\"row-tue\"><th class=\"dayname\">{{ tue }}</th><td>09:00 {{ am }} - 06:00 {{ pm }}</td></tr><tr class=\"row-wed\"><th class=\"dayname\">{{ wed }}</th><td>09:00 {{ am }} - 06:00 {{ pm }}</td></tr><tr class=\"row-thu\"><th class=\"dayname\">{{ thu }}</th><td>09:00 {{ am }} - 06:00 {{ pm }}</td></tr><tr class=\"row-fri\"><th class=\"dayname\">{{ fri }}</th><td>09:00 {{ am }} - 06:00 {{ pm }}</td></tr><tr class=\"row-sat\"><th class=\"dayname\">{{ sat }}</th><td>09:00 {{ am }} - 03:00 {{ pm }}</td></tr><tr class=\"row-sun\"><th class=\"dayname\">{{ sun }}</th><td>{{ closed }}</td></tr></table></div>",

            yield from self.post_process_item(item, response, feature) or []
