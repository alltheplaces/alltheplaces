import re
from typing import Any, Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class CountyMarketSpider(SitemapSpider):
    name = "county_market"
    item_attributes = {"brand": "County Market", "brand_wikidata": "Q5177716"}
    sitemap_urls = ["https://www.mycountymarket.com/sitemap.xml"]
    sitemap_follow = ["wpsl_stores"]
    sitemap_rules = [("/stores/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        raw_data = list(chompjs.parse_js_objects(response.xpath('//*[@id="wpsl-js-extra"]/text()').get()))[-1][
            "locations"
        ][0]
        item = DictParser.parse(raw_data)
        item["name"] = self.item_attributes["brand"]
        item["street_address"] = item.pop("addr_full")
        branch = re.sub(r"^County Market (Liquor )?in ", "", raw_data["store"])
        item["branch"] = branch.replace(f", {item['state']} {item['postcode']}", "")
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["website"] = response.url
        if "Liquor" in raw_data["store"]:
            apply_category(Categories.SHOP_ALCOHOL, item)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//table[contains(@class, "wpsl-opening-hours")]//tr'):
            day = day_time.xpath(".//td/text()").get()
            open_time, close_time = day_time.xpath(".//time/@datetime").getall()
            item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
        yield item
