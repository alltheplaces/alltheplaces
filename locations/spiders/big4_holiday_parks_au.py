from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class Big4HolidayParksAUSpider(CrawlSpider, StructuredDataSpider):
    name = "big4_holiday_parks_au"
    item_attributes = {"brand": "BIG4 Holiday Parks", "brand_wikidata": "Q18636678"}
    allowed_domains = ["www.big4.com.au"]
    start_urls = ["https://www.big4.com.au/caravan-parks"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/www\.big4\.com\.au\/caravan-parks\/(?:act|nsw|nt|qld|sa|tas|vic|wa)$"),
            follow=True,
        ),
        Rule(
            LinkExtractor(allow=r"^https:\/\/www\.big4\.com\.au\/caravan-parks\/(?:act|nsw|nt|qld|sa|tas|vic|wa)\/.+"),
            follow=False,
            callback="parse_sd",
        ),
    ]
    wanted_types = ["LodgingBusiness"]

    def post_process_item(self, item, response, ld_data):
        item.pop("city")  # Not used.
        item.pop("state")  # Source data provides a tourist region, not a state.
        if item["facebook"] in [
            "https://www.facebook.com/BIG4HolidayParks",
            "https://www.facebook.com/ingeniaholidays/",
            "https://www.facebook.com/PLHPs",
        ]:
            item.pop("facebook")
        item.pop("twitter")
        yield item
