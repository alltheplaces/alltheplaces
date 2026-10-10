import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class FoxsPizzaSpider(SitemapSpider):
    name = "foxs_pizza"
    item_attributes = {"brand": "Fox's Pizza Den", "brand_wikidata": "Q5476498"}
    allowed_domains = ["foxspizza.com"]
    sitemap_urls = ["https://www.foxspizza.com/store-sitemap.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        title = response.xpath("//title/text()").get()
        phone = response.xpath('//*[@class="phone_no"]/a/@href').get()
        if "coming soon" in f"{title} {phone}".lower():
            return
        lat, lng = map(float, re.search(r"LatLng\((.*),(.*)\),", response.text).groups())
        item = Feature(
            lat=lat,
            lon=lng,
            ref=response.url,
            website=response.url,
            addr_full=response.xpath('//*[@class="loc_address"]/text()').get().replace("\xa0", " "),
            phone=phone,
            branch=title.removesuffix(" - Fox's Pizza"),
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            " ".join(response.xpath('//*[@class="timings_list"]//text()').getall())
        )
        apply_category(Categories.RESTAURANT, item)
        yield item
