import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PharmaChoiceCASpider(SitemapSpider):
    name = "pharma_choice_ca"
    item_attributes = {"brand": "PharmaChoice", "brand_wikidata": "Q7180716"}
    sitemap_urls = ["https://www.pharmachoice.com/sitemap_index.xml"]
    sitemap_follow = ["location-sitemap"]
    sitemap_rules = [(r"/locations/([^/]+)/$", "parse")]

    def parse(self, response, **kwargs):
        data = response.xpath('//*[@class="pcc-location-map"]/@data-location').get()
        if data:
            item = DictParser.parse(json.loads(data))
            item["ref"] = item["website"] = response.url
            item["branch"] = item.pop("name")
            oh = OpeningHours()
            for day_time in response.xpath('//*[@data-panel="store"]//*[@class ="day"]'):
                day = day_time.xpath('.//*[@class="day-label"]/text()').get()
                times = (
                    day_time.xpath('.//*[@class="day-hours"]/text()').get(default="").replace(" ", "").replace("–", "-")
                )
                if times.lower() in ["closed", "tbd"]:
                    oh.set_closed(day)
                else:
                    open_time, close_time = times.split("-")
                    oh.add_range(
                        day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M%p"
                    )
            item["opening_hours"] = oh

            apply_category(Categories.PHARMACY, item)
            yield item
