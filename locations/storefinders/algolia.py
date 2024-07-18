from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser

# API documentation:
# https://www.algolia.com/doc/rest-api/search/
#
# To use this spider, specify the API key and application ID as sent in the
# headers of a query request, as well as the name of the "index" found in either
# the request URL or in query parameters in the request body. Override
# parse_item to extract attributes from each object. Optionally set the HTTP
# Referer to the store search page.


class AlgoliaSpider(Spider):
    dataset_attributes = {"source": "api", "api": "algolia"}

    api_key = ""
    app_id = ""
    index_name = ""
    referer = None

    def _make_request(self, page=None):
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

    def start_requests(self):
        yield self._make_request(None)

    def parse(self, response):
        result = response.json()["results"][0]
        for location in result["hits"]:
            item = DictParser.parse(location)
            yield from self.parse_item(item, location) or []

        if result["page"] + 1 < result["nbPages"]:
            yield self._make_request(result["page"] + 1)

    def parse_item(self, item, location):
        yield item
