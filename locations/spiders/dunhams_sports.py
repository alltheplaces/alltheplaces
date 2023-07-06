import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DunhamsSportsSpider(scrapy.Spider):
    name = "dunhams_sports"
    item_attributes = {"brand": "Dunham's Sports", "brand_wikidata": "Q5315238"}
    allowed_domains = ["dunhamssports.com"]
    start_urls = [
        "https://www.dunhamssports.com/on/demandware.store/Sites-dunhamssports-Site/en_US/Stores-FindStores?showMap=true&radius=4000&lat=36.0711&long=-86.7196"
    ]

    def parse(self, response):
        for data in response.json().get("stores"):
            oh = OpeningHours()
            days = scrapy.selector.Selector(text=data.get("storeHours")).xpath("//tr")
            for day in days:
                oh.add_range(
                    day=day.xpath("./td[1]/text()").get().strip(":"),
                    open_time=day.xpath("./td[2]/text()").get().split(" to ")[0],
                    close_time=day.xpath("./td[2]/text()").get().split(" to ")[1],
                    time_format="%I:%H %p",
                )

            item = DictParser.parse(data)
            item["opening_hours"] = oh.as_opening_hours()
            item[
                "website"
            ] = f'https://www.dunhamssports.com/store-details?storeID={data.get("ID")}&city={data.get("city")}&state={data.get("stateCode")}'

            yield item
