import html
import json
import re

from parsel import Selector
from scrapy.spiders import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

HTML_TAGS = re.compile("<[^<]+?>")


def strip_tags(s):
    return html.unescape(HTML_TAGS.sub("", s))


class AwaySpider(Spider):
    name = "away"
    item_attributes = {
        "brand": "Away",
        "brand_wikidata": "Q48743138",
        "extras": Categories.SHOP_BAG.value,
        "name": "Away",
    }
    start_urls = ["https://www.awaytravel.com/stores"]

    def parse(self, response):
        data = json.loads(response.xpath('//*[@id="__NEXT_DATA__"]/text()').get())
        for location in data["props"]["pageProps"]["fallback"]["store-location-section-us"]["stores"]:
            item = DictParser.parse(location)

            item["addr_full"] = strip_tags(item["addr_full"])
            item["branch"] = location["homepageCity"]
            item["website"] = response.urljoin(location["linkHref"])
            item["image"] = location["metaImage"]["url"]
            del item["name"]

            oh = OpeningHours()
            oh.add_ranges_from_string(strip_tags(location["hours"]))
            item["opening_hours"] = oh

            links = Selector(text=location["description"]).xpath("//a/@href").getall()

            if not item["email"]:
                for link in links:
                    if link.startswith("mailto:"):
                        item["email"] = link.removeprefix("mailto:")

            if not item["phone"]:
                for link in links:
                    if link.startswith("tel:"):
                        item["phone"] = link.removeprefix("tel:")

            yield item
