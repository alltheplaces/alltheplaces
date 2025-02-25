from typing import Any, Iterable

from scrapy import FormRequest, Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class PandaExpressSpider(Spider):
    name = "panda_express"
    item_attributes = {"brand": "Panda Express", "brand_wikidata": "Q1358690"}
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self) -> Iterable[Request]:
        # Fetch cookies to avoid DataDome captcha blockage
        yield FormRequest(
            url="https://api-js.datadome.co/js/",
            headers={
                "referer": "https://www.pandaexpress.com/",
            },
            formdata={"ddk": "988C29D6706800A8C3451C0AB0E93A"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url="https://nomnom-prod-api.pandaexpress.com/restaurants",
            cookies={"cookie": response.json()["cookie"]},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["restaurants"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines(
                [location.get("streetaddress"), location.get("streetaddress2")]
            )
            item["ref"] = location.get("extref")
            item["website"] = (
                "https://www.pandaexpress.com/locations/{}/{}/{}".format(item["state"], item["city"], item["ref"])
                .lower()
                .replace(" ", "-")
            )
            yield item
