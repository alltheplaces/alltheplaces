import re
from typing import Any

from requests import Response
from scrapy.http import JsonRequest

from locations.spiders.ford_dealers_us import FordDealersUSSpider


class FordCASpider(FordDealersUSSpider):
    name = "ford_ca"

    def parse_state(self, response: Response, **kwargs: Any) -> Any:
        state_list = (
            re.search(r"getDealerConfig.+?,\s*\w[=\s]+\"([\w\s;]+)\"\.split\(\";\"\)", response.text, re.DOTALL)
            .group(1)
            .split(";")
        )
        for make in self.BRAND_MAPPING:
            for state in state_list:
                yield JsonRequest(
                    url="https://www.ford.ca/cxservices/dealer/Dealers.json?make={}&state={}".format(
                        make, state.strip()
                    ),
                    headers={"Application-id": kwargs["token"]},
                    callback=self.parse_details,
                    cb_kwargs={"brand": make},
                )
