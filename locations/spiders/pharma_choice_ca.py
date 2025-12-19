import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class PharmaChoiceCASpider(SitemapSpider):
    name = "pharma_choice_ca"
    item_attributes = {"brand": "PharmaChoice", "brand_wikidata": "Q7180716"}
    sitemap_urls = ["https://www.pharmachoice.com/sitemap_index.xml"]
    sitemap_follow = ["listing-sitemap"]
    sitemap_rules = [(r"/locations/([^/]+)/$", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath("//title/text()").get().removesuffix(" | PharmaChoice")
        item["addr_full"] = response.xpath("//iframe/@title").get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//*[@class="hours"]'):
            day = day_time.xpath('.//*[@class="day"]/text()').get()
            times = day_time.xpath('.//*[@class="time"]/text()').get(default="")
            for open_time, close_time in re.findall(
                r"(\d{1,2}:\d{1,2}[A|P]M)–(\d{1,2}:\d{1,2}[A|P]M)", times.replace(" ", "")
            ):
                item["opening_hours"].add_range(day, open_time, close_time, "%I:%M%p")
        apply_category(Categories.PHARMACY, item)
        yield item
