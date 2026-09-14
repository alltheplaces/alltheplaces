from chompjs import chompjs
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import CLOSED_EN, OpeningHours


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
            item.pop("name", None)
            item["opening_hours"] = OpeningHours()
            for row in response.xpath(r'//*[@class="hours"]/div'):
                day = row.xpath(".//p[1]/text()").get()
                if not (time := row.xpath(".//p[2]/text()").get()):
                    continue
                if time.strip().lower() in CLOSED_EN:
                    item["opening_hours"].set_closed(day)
                    continue
                open_time, close_time = time.split("-")
                item["opening_hours"].add_range(
                    day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M %p"
                )

            item["street_address"] = item.pop("addr_full", None)
            yield item
