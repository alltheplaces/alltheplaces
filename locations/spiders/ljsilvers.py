from chompjs import chompjs
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LjsilversSpider(SitemapSpider):
    name = "ljsilvers"
    item_attributes = {"brand": "Long John Silver's", "brand_wikidata": "Q1535221"}

    sitemap_urls = ["https://www.ljsilvers.com/sitemap.xml"]
    sitemap_rules = [(r"https://www.ljsilvers.com/locations/\w+\/", "parse")]

    def parse(self, response, **kwargs):
        if data := chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "window.__NUXT__")]/text()').re_first(r"location:({.*})}\]")
        ):
            item = DictParser.parse(data)
            item["ref"] = item["website"] = response.url
            item["name"] = "Long John Silver's"
            item["opening_hours"] = OpeningHours()
            for row in response.xpath(r'//*[@class="hours"]/div'):
                day = row.xpath(".//p[1]/text()").get()
                if time := row.xpath(".//p[2]/text()").get():
                    open_time, close_time = time.split("-")
                    item["opening_hours"].add_range(
                        day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M %p"
                    )
                else:
                    continue

            yield item
