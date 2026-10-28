import html
import json
import re
from typing import Any

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BAndMFRSpider(Spider):
    name = "b_and_m_fr"
    item_attributes = {"brand": "B&M", "brand_wikidata": "Q4836931"}
    start_urls = ["https://bmstores.fr/nos-magasins"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for lat, hours_str, lon, pop_str in re.findall(
            r"{ \"lat\": (-?\d+\.\d+), \"hours\": JSON\.parse\(decodeHTMLEntities\(\"({.+?})\"\)\), \"lon\":(-?\d+\.\d+) , \"pop\":\"(.+?)\"",
            response.xpath('//script[contains(text(), "villes")]/text()').get(),
        ):
            item = Feature()
            item["lat"] = lat
            item["lon"] = lon

            item["opening_hours"] = OpeningHours()
            for day, v in json.loads(html.unescape(hours_str)).items():
                for times in v.values():
                    item["opening_hours"].add_range(day, times["from"], times["to"], "%H:%M:%S")

            sel = Selector(text=pop_str)
            item["branch"] = sel.xpath("//b/text()").get().removeprefix("B&M ")
            item["addr_full"] = merge_address_lines(sel.xpath("//div[@class='row']/div/text()").getall())
            item["website"] = item["ref"] = sel.xpath("//a/@href").get()

            apply_category(Categories.SHOP_VARIETY_STORE, item)

            yield item
