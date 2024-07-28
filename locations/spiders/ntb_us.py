import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class NationalTireAndBatteryUSSpider(Spider):
    name = "ntb_us"
    item_attributes = {"brand": "NTB", "brand_wikidata": "Q6978944"}
    start_urls = ["https://www.ntb.com/netstorage/framework.min.js"]
    auth = ""

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            "https://graphql.contentful.com/content/v1/spaces/z5mb0hal4cje/environments/master",
            data={
                "query": """
                    query ComponentStoreDetailsCollection($skip: Int!) {
                        componentStoreDetailsCollection(
                            where: { subBrandInfo: { subBrandShortName: "NTB" } }
                            skip: $skip
                        ) {
                            total
                            skip
                            limit
                            items {
                                ref: storeNumber
                                slug
                                city
                                state: stateAbbreviation
                                postcode: zipCode
                                fullAddress
                                phone: telephone
                                addressLineOne
                                addressLineTwo
                                country
                                location: latLng {
                                    lat
                                    lon
                                }
                            }
                        }
                    }
            """,
                "variables": {"skip": offset},
            },
            headers={"Authorization": "Bearer {}".format(self.auth)},
            callback=self.parse_locations,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        self.auth = re.search(r"prod:{\s+accessToken: '(\w+)',", response.text).group(1)

        yield self.make_request(0)

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        resp = response.json()["data"]["componentStoreDetailsCollection"]
        for location in resp["items"]:
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location["addressLineOne"], location["addressLineTwo"]])

            yield item

        if resp["skip"] + resp["limit"] < resp["total"]:
            yield self.make_request(resp["skip"] + resp["limit"])
