import json
from typing import Any

from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class RymanGBSpider(JSONBlobSpider):
    name = "ryman_gb"
    item_attributes = {"brand": "Ryman", "brand_wikidata": "Q7385188"}
    start_urls = ["https://www.ryman.co.uk/storefinder/"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Host": "www.ryman.co.uk"}, "ROBOTSTXT_OBEY": False}
    requires_proxy = True
    drop_attributes = {"facebook", "twitter"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath('//script[@type="text/x-magento-init"]//text()').getall()
        for script in scripts:
            if "locations" in script:
                result = json.loads(script)
                for store in DictParser.get_nested_key(result, "locations"):
                    item = DictParser.parse(store)
                    item["lat"] = store["latitude"]
                    item["lon"] = store["longitude"]
                    item["branch"] = item.pop("name")
                    item["email"] = store["cs_email"]
                    item["street_address"] = item.pop("addr_full")
                    opening_hours = OpeningHours()
                    times = json.loads(store["schedule_data"])
                    for day in DAYS_FULL:
                        if (
                            "lunch_break_ends" in times[day.lower()]
                            and times[day.lower()]["lunch_break_starts"] is not None
                        ):
                            opening_hours.add_range(
                                day=day,
                                open_time=times[day.lower()]["open_time"],
                                close_time=times[day.lower()]["lunch_break_starts"],
                                time_format="%H:%M",
                            )
                            opening_hours.add_range(
                                day=day,
                                open_time=times[day.lower()]["lunch_break_ends"],
                                close_time=times[day.lower()]["closing_time"],
                                time_format="%H:%M",
                            )
                        else:
                            opening_hours.add_range(
                                day=day,
                                open_time=times[day.lower()]["open_time"],
                                close_time=times[day.lower()]["closing_time"],
                                time_format="%H:%M",
                            )
                    item["opening_hours"] = opening_hours
                    yield item
