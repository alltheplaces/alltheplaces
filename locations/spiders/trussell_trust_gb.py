import json
import re
from typing import Any, AsyncIterator

import chompjs
from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class TrussellTrustGBSpider(Spider):
    name = "trussell_trust_gb"
    item_attributes = {"operator": "The Trussell Trust", "operator_wikidata": "Q15621299"}

    def make_request(self, page: int) -> Request:
        return Request(
            url="https://www.trussell.org.uk/emergency-food/i-have-a-food-voucher/choose-a-foodbank?lat=&lng=&page={}".format(
                page
            ),
            cb_kwargs={"page": page},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, page: int, **kwargs: Any) -> Any:
        stream = ""
        for script in response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall():
            chunk = chompjs.parse_js_object(script)
            if len(chunk) > 1 and isinstance(chunk[1], str):
                stream += chunk[1]
        if '"markers":' not in stream:
            return

        markers, _ = json.JSONDecoder().raw_decode(stream.split('"markers":', 1)[1])
        for marker in markers:
            info = marker["infoContent"]
            if isinstance(info, str):
                # Lazily loaded markers point to a separate "<id>:" line of the stream
                definition = re.search(r"(?:^|\n){}:".format(re.escape(info.removeprefix("$L"))), stream)
                info, _ = json.JSONDecoder().raw_decode(stream[definition.end() :])
            info = {k: v for k, v in info[3].items() if v != "$undefined"}

            item = Feature()
            item["ref"] = marker["key"]
            item["branch"] = marker["title"]
            item["name"] = info.get("description", "").removeprefix("Part of ") or None
            item["lat"] = marker["location"]["lat"]
            item["lon"] = marker["location"]["lng"]
            item["phone"] = info.get("phoneNumber")
            item["email"] = info.get("emailAddress")
            if item["email"] and item["email"].endswith(".foodbank.org.uk"):
                item["website"] = "https://{}/".format(item["email"].split("@")[1])
            address = info.get("address") or {}
            item["street_address"] = merge_address_lines([address.get("line1"), address.get("line2")])
            item["city"] = address.get("city")
            item["postcode"] = address.get("postCode")

            item["opening_hours"] = OpeningHours()
            for day in info.get("collectionTimes") or []:
                for times in day["openingHours"]:
                    if times["open"] and times["close"]:
                        item["opening_hours"].add_range(day["day"], times["open"], times["close"], "%I:%M %p")

            apply_category(Categories.SOCIAL_FACILITY, item)
            yield item

        yield self.make_request(page + 1)
