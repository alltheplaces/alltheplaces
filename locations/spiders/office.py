import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class OfficeSpider(SitemapSpider):
    name = "office"
    item_attributes = {"brand": "Office", "brand_wikidata": "Q7079121"}
    allowed_domains = ["office.co.uk"]
    sitemap_urls = ["https://www.office.co.uk/robots.txt"]
    sitemap_follow = ["store"]
    sitemap_rules = [(r"/view/content/storelocator\?storename", "parse")]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["website"] = item["ref"] = response.url
        name = response.xpath('//span[@class="bold"]/text()').get()
        item["name"], item["branch"] = name.split(" ", 1)
        item["name"] = item["name"].title()
        if "Offspring" in item["name"]:
            item["brand"] = "Offspring Shoes"
            item["brand_wikidata"] = "Q138802866"
        item["phone"] = response.xpath('//div[contains(span/text(), "Tel")]/text()').get()
        item["addr_full"] = merge_address_lines(
            response.xpath('//ul[contains(@class, "storelocator_addressdetails_address")]/li/text()').getall()[1:]
        )

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//span[@class="storelocator_open_times_day"]/text()').getall():
            if m := re.search(r"(\w+): (\d{1,2}:\d\d) - (\d\d:\d\d)", rule):
                item["opening_hours"].add_range(*m.groups())

        if latlng := re.search(
            r"LatLng\((-?\d+\.\d+),\s?(-?\d+\.\d+)\),",
            response.xpath('//script[contains(text(), "google.maps.LatLng(")]/text()').get(),
        ):
            item["lat"], item["lon"] = latlng.groups()

        apply_category(Categories.SHOP_SHOES, item)

        yield item
