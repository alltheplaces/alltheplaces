import json
from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class FoodstuffsNZSpider(CrawlSpider):
    name = "foodstuffs_nz"
    requires_proxy = True
    start_urls = ["https://www.newworld.co.nz/store-finder", "https://www.paknsave.co.nz/store-finder"]
    BRANDS = {"newworld": ("New World", "Q7012488"), "paknsave": ("PAK'nSAVE", "Q7125339")}
    rules = [Rule(LinkExtractor(restrict_xpaths='//*[@class="ds-grid ds-gap-12"]//ul'), "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        if data := response.xpath('//script[@id="__NEXT_DATA__" and @type="application/json"]/text()').get():
            raw_data = json.loads(data)["props"]["pageProps"]["page"]
            raw_data.update(raw_data.pop("contact_details"))
            item = DictParser.parse(raw_data)
            item["website"] = response.url
            if item["name"]:
                item["branch"] = item.pop("name").removeprefix("PAK'nSAVE ").removeprefix("New World ")
            brand = response.url.split(".")[1]
            if brand_details := self.BRANDS.get(brand):
                item["brand"], item["brand_wikidata"] = brand_details
            try:
                oh = OpeningHours()
                for day, time in raw_data.get("opening_hours").items():
                    open_time = time["open_from"].replace(".", ":")
                    close_time = time["open_until"].replace(".", ":")
                    oh.add_range(day, open_time, close_time, "%I:%M%p")
                item["opening_hours"] = oh
            except:
                pass
            yield item
