from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class GlobusBaumarktDESpider(CrawlSpider, StructuredDataSpider):
    name = "globus_baumarkt_de"
    item_attributes = {"brand": "Globus Baumarkt", "brand_wikidata": "Q457503"}
    start_urls = ["https://www.globus-baumarkt.de/alle-maerkte/"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//a[@target="_self"]', allow="/info/markt/"), callback="parse")]
    wanted_types = [["LocalBusiness", "HardwareStore"]]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("GLOBUS BAUMARKT ", "")
        oh = OpeningHours()
        apply_category(Categories.SHOP_DOITYOURSELF, item)
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
        yield item

    # def parse(self, response):
    #     raw_data = response.xpath('//script[@type="application/ld+json"][contains(text(), "Place")]/text()').get()
    #
    #     if not raw_data:
    #         return
    #
    #     # The image field currently breaks the JSON
    #     data = json.loads(re.sub(r'"image": (\[".+"\],)', "", raw_data))
    #     item = LinkedDataParser.parse_ld(data)
    #     item["ref"] = response.url
    #     item["extras"]["fax"] = data.get("fax")
    #     item["branch"] = item.pop("name").replace("Globus Baumarkt ", "")
    #     for i in response.xpath('//div[@class="medium-6 cell"]/p').getall():
    #         day_hour_list = re.findall(r'<span class="opening-day is--wide">(.*?) Uhr', i)
    #         if day_hour_list:
    #             item["opening_hours"] = OpeningHours()
    #             for day_hour in day_hour_list:
    #                 day_range, hour_range = day_hour.split(":</span>")
    #                 item["opening_hours"].add_ranges_from_string(
    #                     day_range.replace(".", "") + " " + hour_range, days=DAYS_DE
    #                 )
    #     apply_category(Categories.SHOP_DOITYOURSELF, item)
    #     yield item
