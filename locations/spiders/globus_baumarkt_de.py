import json
import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.linked_data_parser import LinkedDataParser


class GlobusBaumarktDESpider(CrawlSpider):
    name = "globus_baumarkt_de"
    item_attributes = {"brand": "Globus Baumarkt", "brand_wikidata": "Q457503"}
    start_urls = ["https://www.globus-baumarkt.de/alle-maerkte/"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//a[@target="_self"]', allow="/info/markt/"), callback="parse")]

    def parse(self, response):
        raw_data = response.xpath('//script[@type="application/ld+json"][contains(text(), "Place")]/text()').get()

        if not raw_data:
            return

        # The image field currently breaks the JSON
        data = json.loads(re.sub(r'"image": (\[".+"\],)', "", raw_data))
        item = LinkedDataParser.parse_ld(data)
        item["ref"] = response.url
        item["extras"]["fax"] = data.get("fax")
        item["branch"] = item.pop("name").replace("Globus Baumarkt ", "")
        for i in response.xpath('//div[@class="medium-6 cell"]/p').getall():
            day_hour_list = re.findall(r'<span class="opening-day is--wide">(.*?) Uhr', i)
            if day_hour_list:
                item["opening_hours"] = OpeningHours()
                for day_hour in day_hour_list:
                    day_range, hour_range = day_hour.split(":</span>")
                    item["opening_hours"].add_ranges_from_string(
                        day_range.replace(".", "") + " " + hour_range, days=DAYS_DE
                    )
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
