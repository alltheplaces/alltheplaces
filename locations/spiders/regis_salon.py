from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class RegisSalonSpider(SitemapSpider):
    name = "regis_salon"
    item_attributes = {"brand": "Regis", "brand_wikidata": "Q7309325", "extras": Categories.SHOP_HAIRDRESSER.value}
    sitemap_urls = ["https://www.signaturestyle.com/sitemap.xml"]
    sitemap_rules = [(r"https://www.signaturestyle.com/locations/[^/]+/[^/]+/[^/]+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@itemprop="headline"]/@content').get().split("-", 1)[1]
        item["street_address"] = response.xpath('//*[@class="sqs-html-content"]/p//text()').get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath('//*[@class="sqs-html-content"]/p/span[2]/text()').get()]
        )
        item["lat"] = response.xpath('//*[@property="og:latitude"]/@content').get()
        item["lon"] = response.xpath('//*[@property="og:longitude"]/@content').get()
        item["phone"] = response.xpath('//*[@class="sqs-html-content"]/p[2]//text()').get()
        item["website"] = item["ref"] = response.url
        oh = OpeningHours()
        for time_text in response.xpath(
                '//*[@class="col sqs-col-5 span-5"]//*[@class="sqs-html-content"]//p//text()'
        ).getall():
            oh.add_ranges_from_string(time_text)
        item["opening_hours"] = oh
        yield item
