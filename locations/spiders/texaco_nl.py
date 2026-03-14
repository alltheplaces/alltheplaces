import ast

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class TexacoNLSpider(SitemapSpider):
    name = "texaco_nl"
    item_attributes = {"brand": "Texaco", "brand_wikidata": "Q775060"}
    sitemap_urls = ["https://texaco.nl/locations-sitemap.xml"]

    def parse(self, response):
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["name"] = response.xpath("//title/text()").get()
        addr = response.xpath('//section[@class="locationDetail noHero"]//p/text()').getall()
        item["street_address"] = addr[0]
        item["addr_full"] = " ".join(addr)
        item["phone"] = response.xpath('//section[@class="locationDetail noHero"]//a/text()').get()
        oh = OpeningHours()
        days = {"mon": "Mo", "tue": "Tu", "wed": "We", "thu": "Th", "fri": "Fr", "sat": "Sa", "sun": "Su"}
        for k, v in days.items():
            start, end = [t.strip() for t in response.xpath(f'//*[@id="{k}"]/text()').get().split("-")]
            try:
                oh.add_range(v, start, end)
            except:
                pass
        item["opening_hours"] = oh
        item["lat"], item["lon"] = ast.literal_eval(
            response.xpath('//*[contains(text(), "setView")]/text()').re_first(r"setView\((\[.*\])")
        )
        apply_category(Categories.FUEL_STATION, item)
        yield item
