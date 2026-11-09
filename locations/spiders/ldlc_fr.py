from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LdlcFRSpider(CrawlSpider, StructuredDataSpider):
    name = "ldlc_fr"
    item_attributes = {"brand": "LDLC", "brand_wikidata": "Q127164489"}
    allowed_domains = ["www.ldlc.com"]
    start_urls = ["https://www.ldlc.com/magasins-ldlc/"]
    rules = [Rule(LinkExtractor(allow=r"/magasins-ldlc/magasin-\d+/[^/]+/$"), callback="parse_sd")]
    wanted_types = ["ComputerStore"]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.split("/magasin-")[1].split("/")[0]
        branch = item.pop("name").removeprefix("LDLC").strip()
        if branch.startswith("Apple "):
            # Apple Premium Partner shops run by LDLC
            item["name"] = "LDLC Apple"
            branch = branch.removeprefix("Apple ")
        item["branch"] = branch
        item["lat"] = response.xpath('//div[@id="map"]/@data-lat').get()
        item["lon"] = response.xpath('//div[@id="map"]/@data-lng').get()
        item.pop("image", None)

        oh = OpeningHours()
        for day in response.xpath('//div[@class="timesheets"]/div[contains(@class, "time")]'):
            day_name = DAYS_FR.get(day.xpath('./span[@class="day"]/text()').get("").strip().title())
            if not day_name:
                continue
            for times in day.xpath('./span[contains(@class, "hours")]/span[@class="regular"]/text()').getall():
                if "-" in times:
                    open_time, close_time = times.split("-")
                    oh.add_range(day_name, open_time.strip(), close_time.strip())
        item["opening_hours"] = oh

        yield item
