import chompjs
from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BashasUSSpider(Spider):
    name = "bashas_us"
    item_attributes = {
        "brand": "Bashas'",
        "brand_wikidata": "Q4866786",
    }
    start_urls = ["https://www.bashas.com/store-finder/"]

    def parse(self, response: TextResponse):
        api_key = chompjs.parse_js_object(response.xpath('//*[@id = "hsapi-script-js-extra"]/text()').get()).get(
            "hs_api_key"
        )
        yield JsonRequest(
            url="https://user-api.gethomesome.com/locations",
            headers={"apikey": f"{api_key}"},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: TextResponse):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["uniqueName"]
            try:
                oh = OpeningHours()
                for day_time in location.get("operatingHours"):
                    day = day_time.get("day")
                    open_time, close_time = day_time.get("hours").split("-")
                    oh.add_range(
                        day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I%p"
                    )
                item["opening_hours"] = oh
            except:
                pass
            yield item

    # def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
    #     if branch_name := item.pop("name", None):
    #         if branch_name.startswith("Bashas’ Diné Market"):
    #             item["brand"] = "Bashas’ Diné Market"
    #             item["branch"] = branch_name.removeprefix("Bashas’ Diné Market").removeprefix(": ")
    #         elif branch_name.startswith("Bashas’ Supermarket"):
    #             item["brand"] = "Bashas’ Supermarket"
    #             item["branch"] = branch_name.removeprefix("Bashas’ Supermarket").removeprefix(": ")
    #         if not item["branch"].strip():
    #             item.pop("branch", None)
    #     apply_category(Categories.SHOP_SUPERMARKET, item)
    #     yield item
