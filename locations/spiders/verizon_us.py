import json

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class VerizonUSSpider(SitemapSpider, StructuredDataSpider):
    name = "verizon_us"
    item_attributes = {"brand": "Verizon", "brand_wikidata": "Q919641"}
    sitemap_urls = ["https://www.verizon.com/business/locations/sitemap.xml"]
    sitemap_rules = [(r"https://www.verizon.com/business/locations/[^/]+/[^/]+/[^/]+/$", "parse")]

    def parse(self, response: TextResponse, **kwargs):
        if street_address := response.xpath('//*[@class="vbg-address-text"]/strong/text()').get():
            item = Feature()
            item["branch"] = (
                response.xpath("//title//text()")
                .get()
                .removeprefix("Verizon Business Services - ")
                .removesuffix("| Verizon")
            )
            item["street_address"] = street_address
            item["addr_full"] = merge_address_lines(
                response.xpath('//*[@class="vbg-address-text"]//text()').getall()
            ).replace("Address, ", "")
            item["lat"] = response.xpath("//@data-lat").get()
            item["lon"] = response.xpath("//@data-lng").get()
            item["ref"] = item["website"] = response.url
            apply_category(Categories.SHOP_MOBILE_PHONE, item)
            day_time_data = response.xpath("//@data-hours-json").get()
            oh = OpeningHours()
            if data := json.loads(day_time_data):
                for day, time in data.items():
                    day = day
                    if time in ["Closed", "Closed Closed"]:
                        oh.set_closed(day)
                    else:
                        open_time, close_time = time.split("-")
                        oh.add_range(day, open_time.strip(), close_time.strip(), "%I:%M %p")
            item["opening_hours"] = oh
            yield item
