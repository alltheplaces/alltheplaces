import re

from scrapy import Request
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class SchnitzAUSpider(SitemapSpider):
    name = "schnitz_au"
    item_attributes = {"brand": "Schnitz", "brand_wikidata": "Q48792277"}
    allowed_domains = ["schnitz.com.au", "schnitztechnology.com"]
    sitemap_urls = ["https://schnitz.com.au/project-sitemap.xml"]
    sitemap_rules = [(r"\/location\/[\w\-]+", "parse")]

    def parse(self, response):
        hours_page_url = response.xpath(
            '//iframe[contains(@src, "https://schnitztechnology.com/iframe.php?sid=")]/@src'
        ).get()
        properties = {
            "ref": hours_page_url.replace("https://schnitztechnology.com/iframe.php?sid=", ""),
            "name": response.xpath('//div[@class="et_pb_header_content_wrapper"]/text()').get().strip(),
            "lat": response.xpath("//div/@data-lat").get().strip(),
            "lon": response.xpath("//div/@data-lng").get().strip(),
            "addr_full": response.xpath(
                '//div[@class="et_pb_row et_pb_row_0_tb_body"]/div[1]//div[@class="et_pb_text_inner"]/text()'
            )
            .get()
            .strip(),
            "phone": response.xpath(
                '//div[@class="et_pb_row et_pb_row_0_tb_body"]/div[2]//div[@class="et_pb_text_inner"]/text()'
            ).get(),
            "website": response.url,
        }
        item = Feature(**properties)
        yield Request(url=hours_page_url, meta={"item": item}, callback=self.add_hours)

    def add_hours(self, response):
        hours_string = " ".join(response.xpath("//table/tr/td//text()").getall()).replace("day ", "day: ")
        hours_string = re.sub(r"([AP]M)\s+(\d+)", r"\1 - \2", hours_string)
        item = response.meta["item"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
