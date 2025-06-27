from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CountyMarketSpider(SitemapSpider):
    name = "county_market"
    item_attributes = {"brand": "County Market", "brand_wikidata": "Q5177716"}
    sitemap_urls = ["https://www.mycountymarket.com/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = list(chompjs.parse_js_objects(response.xpath('//*[@id="wpsl-js-js-extra"]/text()').get()))[1][
            "locations"
        ][0]
        item = DictParser.parse(raw_data)
        item["name"] = self.item_attributes["brand"]
        item["street_address"] = item.pop("addr_full")
        item["branch"] = raw_data["store"].replace("County Market in ", "")
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["website"] = response.url
        apply_category(Categories.SHOP_SUPERMARKET, item)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//*[@class="wpsl-opening-hours"]//tr'):
            day = day_time.xpath(".//td/text()").get()
            open_time, close_time = day_time.xpath(".//time/text()").get().split(" - ")
            item["opening_hours"].add_range(
                day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M %p"
            )
        yield item
