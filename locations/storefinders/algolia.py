from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser
from locations.items import Feature


class AlgoliaSpider(Spider, AutomaticSpiderGenerator):
    """
    Documentation of the Algolia API is available at:
    https://www.algolia.com/doc/rest-api/search/

    To use this spider, specify the API key and application ID as sent in the
    headers of a query request, as well as the name of the "index" found in
    either the request URL or in query parameters in the request body.
    Override post_process_item to extract attributes from each object.
    Optionally set `referer` as the HTTP Referer header of the store search
    page.
    """

    dataset_attributes = {"source": "api", "api": "algolia"}

    api_key: str = ""
    app_id: str = ""
    index_name: str = ""
    referer: str | None = None

    detection_rules = [
        DetectionRequestRule(
            url=r"^https?:\/\/(?:[a-z0-9]+)-dsn\.algolia\.net\/1\/indexes\/(?P<index_name>[^/*]+)\/(?:browse|objects|queries|query)(?:\?|$)",
            headers='{api_key: .["x-algolia-api-key"], app_id: .["x-algolia-application-id"]}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/(?:[a-z0-9]+)-dsn\.algolia\.net\/1\/indexes\/\*\/(?:browse|objects|queries|query)(?:\?|$)",
            headers='{api_key: .["x-algolia-api-key"], app_id: .["x-algolia-application-id"]}',
            data='keys[] | capture("\\"indexName\\":\\"(?<index_name>[^\\"]*)\\"")',
        ),
    ]

    def _make_request(self, page: int | None = None) -> JsonRequest:
        params = "hitsPerPage=1000"
        if page is not None:
            params += f"&page={page}"

        headers = {"x-algolia-api-key": self.api_key, "x-algolia-application-id": self.app_id}
        if self.referer is not None:
            headers["Referer"] = self.referer

        return JsonRequest(
            url=f"https://{self.app_id}-dsn.algolia.net/1/indexes/*/queries",
            headers=headers,
            data={
                "requests": [
                    {
                        "indexName": self.index_name,
                        "params": params,
                    }
                ],
            },
        )

    def start_requests(self) -> Iterable[JsonRequest]:
        yield self._make_request(None)

    def parse(self, response: Response) -> Iterable[Feature | JsonRequest]:
        result = response.json()["results"][0]
        for feature in result["hits"]:
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            yield from self.post_process_item(item, response, feature) or []

        if result["page"] + 1 < result["nbPages"]:
            yield self._make_request(result["page"] + 1)

    def pre_process_data(self, location: dict) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
