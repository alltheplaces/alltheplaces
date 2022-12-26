import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CharleysPhillySteaksSpider(scrapy.Spider):
    name = "charleys_philly_steaks"
    allowed_domains = ["charleys.com"]
    item_attributes = {"brand": "Charley's Philly Steaks", "brand_wikidata": "Q1066777"}

    def start_requests(self):
        url = "https://www.charleys.com/wp-admin/admin-ajax.php"
        payload = "action=get_nearby_locations&lat=40.7127753&lng=-74.0059728&distance=5000"
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        yield scrapy.Request(url=url, headers=headers, method="POST", body=payload, callback=self.parse_list)

    def parse_list(self, response):
        for data in response.json().get("data"):
            yield scrapy.Request(
                url=data.get("permalink"),
                callback=self.parse_store,
                cb_kwargs={"data": data},
            )

    def parse_store(self, response, data):
        oh = OpeningHours()
        if days := response.xpath('//div[@id="business-0"]//tr'):
            for day in days:
                if day.xpath("./td/text()").get().strip() == "Closed":
                    continue
                oh.add_range(
                    day=day.xpath("./th/text()").get().strip(),
                    open_time=re.split(" - |-", day.xpath("./td/text()").get().strip())[0],
                    close_time=re.split(" - |-", day.xpath("./td/text()").get().strip())[1],
                    time_format="%I:%M%p",
                )

        item = DictParser.parse(data)
        item["website"] = response.url
        item["opening_hours"] = oh.as_opening_hours()

        yield item
