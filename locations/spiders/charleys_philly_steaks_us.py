import re

from scrapy import Request, Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CharleysPhillySteaksUSSpider(Spider):
    name = "charleys_philly_steaks_us"
    item_attributes = {"brand": "Charley's Philly Steaks", "brand_wikidata": "Q1066777"}
    allowed_domains = ["www.charleys.com"]
    start_urls = ["https://www.charleys.com/wp-admin/admin-ajax.php"]

    def start_requests(self):
        formdata = {
            "action": "get_blended_nearby_locations",
            "lat": "40.7127753",
            "lon": "-74.0059728",
            "distance": ""
        }
        for url in self.start_urls:
            yield FormRequest(url=url, method="POST", formdata=formdata, callback=self.parse_list)

    def parse_list(self, response):
        print(response.text)
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
