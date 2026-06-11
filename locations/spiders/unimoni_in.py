from typing import Any, AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class UnimoniINSpider(scrapy.Spider):
    name = "unimoni_in"
    item_attributes = {"brand": "Unimoni", "brand_wikidata": "Q7863721"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[Any]:
        url = "https://www.unimoni.in/unimoni-in/umsjsp/BranchLocatorAPI.jsp"
        yield JsonRequest(url=url, callback=self.parse_state)

    def parse_state(self, response: Response, **kwargs: Any) -> Any:
        for state in response.json().get("state"):
            state_name = state.get("stateName")
            state_code = state.get("stateCode")
            yield JsonRequest(
                url=f"https://www.unimoni.in/unimoni-in/umsjsp/BranchLocatorAPI.jsp?selFlag=B&State={state_code}",
                cb_kwargs={"state_name": state_name, "state_code": state_code},
                callback=self.parse_city,
            )

    def parse_city(self, response: Response, **kwargs: Any) -> Any:
        for branch in response.json().get("branch"):
            branch_code = branch.get("branchcode")
            yield JsonRequest(
                url=f"https://www.unimoni.in/unimoni-in/umsjsp/BranchLocatorAPI.jsp?selFlag=A&State={kwargs['state_name']}&Branch={branch_code}",
                cb_kwargs={
                    "state": kwargs["state_name"],
                    "branch_code": branch_code,
                    "branch": branch.get("branchName"),
                },
                callback=self.parse_details,
            )

    def parse_details(self, response: Response, **kwargs: Any) -> Any:
        try:
            data = response.json()
        except ValueError:
            return
        item = DictParser.parse(data)
        item["name"] = None
        item["branch"] = kwargs["branch"]
        item["ref"] = kwargs["branch_code"]
        item["state"] = kwargs["state"]
        item["addr_full"] = ", ".join(filter(None, [data.get("address1"), data.get("address2"), data.get("address3")]))
        apply_category(Categories.BUREAU_DE_CHANGE, item)
        yield item
