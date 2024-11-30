from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class GifiSpider(Spider):
    name = "gifi"
    item_attributes = {"brand": "GiFi", "brand_wikidata": "Q3105439"}
    skip_auto_cc_domain = True

    def make_request(self, page: int, index_name: str) -> JsonRequest:
        return JsonRequest(
            url="https://0knemtbxx3-dsn.algolia.net/1/indexes/*/queries",
            headers={"x-algolia-api-key": "7a46160ed01bb0af2c2af8d14b97f3c5", "x-algolia-application-id": "0KNEMTBXX3"},
            data={
                "requests": [
                    {
                        "indexName": index_name,
                        "query": "",
                        "params": "facets=&filters=&page={}".format(page),
                    },
                ]
            },
            meta={"index_name": index_name},
        )

    def start_requests(self) -> Iterable[Request]:
        for index_name in [
            "AFEB_fr",  # https://www.gifi.fr/
            "GFES_es",  # https://www.gifi.es/
            "GFCH_fr",  # https://www.gifi.ch/
        ]:
            # TODO: add Italy when available at http://www.gifi.it/
            yield self.make_request(0, index_name)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        resp = response.json()["results"][0]
        for location in resp["hits"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Gifi ")
            item["city"] = location["city"]["name"]
            item["street_address"] = merge_address_lines([location["street1"], location["street2"]])
            item["addr_full"] = merge_address_lines(location["formatted_address"])
            item["lat"] = location["_geoloc"]["lat"]
            item["lon"] = location["_geoloc"]["lng"]
            item["image"] = location["pictures"][0]
            item["website"] = urljoin("https://magasins.gifi.fr/fr/", location["url_location"])

            try:
                item["opening_hours"] = self.parse_opening_hours(location["formatted_opening_hours"])
            except:
                self.logger.error("Error parsing opening hours: {}".format(location["formatted_opening_hours"]))

            apply_category(Categories.SHOP_VARIETY_STORE, item)

            yield item

        if resp["page"] < resp["nbPages"]:
            yield self.make_request(resp["page"] + 1, response.meta["index_name"])

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, times in rules.items():
            if not times:
                oh.set_closed(day)
            else:
                for time in times:
                    oh.add_range(day, *time.split("-"))

        return oh
