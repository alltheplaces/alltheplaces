from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GlobusBaumarktDESpider(CrawlSpider, StructuredDataSpider):
    name = "globus_baumarkt_de"
    item_attributes = {"brand": "Globus Baumarkt", "brand_wikidata": "Q457503"}
    start_urls = ["https://www.globus-baumarkt.de/alle-maerkte/"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//a[@target="_self"]', allow="/info/markt/"), callback="parse")]
    wanted_types = [["LocalBusiness", "HardwareStore"]]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("GLOBUS BAUMARKT ", "")
        oh = OpeningHours()
        try:
            start_day, end_day = (
                response.xpath('//*[@class="opening-day is--wide"]/text()')
                .get()
                .replace(".", "")
                .replace(":", "")
                .split(" - ")
            )
            start_day = sanitise_day(start_day, DAYS_DE)
            end_day = sanitise_day(end_day, DAYS_DE)
            open_time, close_time = (
                response.xpath('//*[@class="intro"]//div//p[2]/text()').get().replace("Uhr", "").split("-")
            )
            oh.add_days_range(day_range(start_day.strip(), end_day.strip()), open_time.strip(), close_time.strip())
            item["opening_hours"] = oh
        except:
            pass
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
