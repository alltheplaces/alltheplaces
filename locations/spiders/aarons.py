from typing import Any, Iterable

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class AaronsSpider(Spider):
    name = "aarons"
    item_attributes = {"brand": "Aaron's", "brand_wikidata": "Q10397787"}

    def make_request(self, offset: int, limit: int = 10) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.aarons.com/locations/search?limit={limit}&offset={offset}",
            cb_kwargs=dict(offset=offset, limit=limit),
        )

    def start_requests(self) -> Iterable[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]["entities"]:
            location.update(location.pop("profile"))
            item = DictParser.parse(location)
            item["ref"] = location.get("c_storeCode")
            address = location["address"]
            item["street_address"] = merge_address_lines(
                [address.get("line1"), address.get("line2"), address.get("line3")]
            )
            item["website"] = response.urljoin(location.get("url"))
            item["phone"] = "; ".join(
                filter(
                    None,
                    [location.get("mainPhone", {}).get("number"), location.get("alternatePhone", {}).get("number")],
                )
            )
            item["opening_hours"] = OpeningHours()
            for rule in location.get("hours", {}).get("normalHours", []):
                if rule.get("isClosed"):
                    item["opening_hours"].set_closed(rule["day"])
                else:
                    for shift in rule["intervals"]:
                        item["opening_hours"].add_range(
                            rule["day"], str(shift["start"]).zfill(4), str(shift["end"]).zfill(4), "%H%M"
                        )
            yield item

        new_offset = kwargs["offset"] + kwargs["limit"]
        if new_offset < response.json()["response"]["count"]:
            yield self.make_request(new_offset)
