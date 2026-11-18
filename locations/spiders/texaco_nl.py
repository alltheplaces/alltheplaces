import ast

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


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
        item["addr_full"] = merge_address_lines(addr)
        item["phone"] = response.xpath('//section[@class="locationDetail noHero"]//a/text()').get()
        oh = OpeningHours()
        for k, v in zip(DAYS_3_LETTERS, DAYS):
            start, end = [t.strip() for t in response.xpath(f'//*[@id="{k.lower()}"]/text()').get().split("-")]
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
