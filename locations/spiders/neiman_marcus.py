import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class NeimanMarcusSpider(CrawlSpider):
    name = "neiman_marcus"
    item_attributes = {"brand": "Neiman Marcus", "brand_wikidata": "Q743497"}
    allowed_domains = ["stores.neimanmarcus.com"]
    start_urls = ["https://stores.neimanmarcus.com/stores/locations"]
    rules = [Rule(LinkExtractor(allow=r"/stores/[-\w]+/[-\w]+/[-\w]+/[0-9]+$"), callback="parse", follow=True)]

    def parse(self, response):
        ldjson = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        data = (
            ldjson.get("props", {})
            .get("pageProps", {})
            .get("storeInfo", {})
            .get("storeServices", {})
            .get("curbside", {})
        )
        item = DictParser.parse(data.get("addressDetails")[0])
        item["website"] = response.url
        item["name"] = data.get("props", {}).get("pageProps", {}).get("storeInfo", {}).get("name")
        item["phone"] = data.get("phoneNumbers")[0]
        item["ref"] = ldjson.get("props", {}).get("pageProps", {}).get("storeInfo", {}).get("storeNumber")
        oh = OpeningHours()
        for day in data.get("workingHours"):
            for helfday in day.get("hours"):
                if helfday.strip() == "CLOSED":
                    continue
                oh.add_range(
                    day=day.get("label"),
                    open_time=helfday.strip().split(" - ")[0],
                    close_time=helfday.strip().split(" - ")[1],
                    time_format="%I%p",
                )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
