import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class PollysPiesUSSpider(SitemapSpider):
    name = "pollys_pies_us"
    item_attributes = {"brand": "Polly's Pies", "name": "Polly's Pies"}
    sitemap_urls = ["https://www.pollyspies.com/locations-sitemap.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.css("h1.loc_title::text").get()

        addr_lines = response.css(".address_block a::text").getall()
        if len(addr_lines) == 2:
            item["street_address"] = addr_lines[0].strip()
            if m := re.match(r"^(.+),\s*([A-Z]{2})\s*(\d{5})$", addr_lines[1].strip()):
                item["city"], item["state"], item["postcode"] = m.groups()

        item["phone"] = response.css(".phone_block p.desk_only::text").get()

        if m := re.search(r"single_location_lat\s*=\s*(-?\d+\.\d+);", response.text):
            item["lat"] = m.group(1)
        if m := re.search(r"single_location_lng\s*=\s*(-?\d+\.\d+);", response.text):
            item["lon"] = m.group(1)

        hours_string = "; ".join(
            f"{d.css('span::text').get('').strip()} {d.xpath('./br/following-sibling::text()').get('').strip()}"
            for d in response.css(".hours_block .upp .hours_block")
        )
        oh = OpeningHours()
        oh.add_ranges_from_string(hours_string)
        item["opening_hours"] = oh

        apply_category(Categories.RESTAURANT, item)

        yield item
