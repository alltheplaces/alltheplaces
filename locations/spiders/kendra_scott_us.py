from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class KendraScottUSSpider(Spider):
    name = "kendra_scott_us"
    item_attributes = {"brand": "Kendra Scott", "brand_wikidata": "Q120885584"}
    start_urls = ["https://www.kendrascott.com/stores/directory"]

    def parse(self, response):
        for el in response.xpath("//div[@class='search-item']"):
            item = Feature()
            item["lat"] = el.xpath("@data-storelat").get()
            item["lon"] = el.xpath("@data-storelong").get()
            item["branch"] = "".join(el.xpath("*//div[@class='store-name']//text()").getall()).strip().title()
            item["addr_full"] = el.xpath("*//p[@class='store-address']/text()").get()

            urlpath = el.xpath("*//div[@class='action-btns']/a/@href").get()
            item["website"] = response.urljoin(urlpath)
            item["ref"] = urlpath.split("/")[-1]

            for link in el.css("* .margin-contact ::attr(href)").getall():
                if link.startswith("tel:"):
                    item["phone"] = link.removeprefix("tel:").strip()
                elif link.startswith("mailto:"):
                    item["email"] = link.removeprefix("mailto:").strip()

            oh = OpeningHours()
            for line in el.xpath("*//div[@class='store-hours']//p/text()").getall():
                oh.add_ranges_from_string(line)
            item["opening_hours"] = oh

            yield item
