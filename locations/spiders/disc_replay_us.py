from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class DiscReplayUSSpider(CrawlSpider):
    name = "disc_replay_us"
    item_attributes = {
        "brand": "Disc Replay",
        "brand_wikidata": "Q108202431",
        "extras": Categories.SHOP_VIDEO_GAMES.value,
    }
    allowed_domains = ["www.discreplay.com"]
    start_urls = ["https://www.discreplay.com/locations"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"^https:\/\/www\.discreplay\.com\/[^/]+$",
                restrict_xpaths='//div[contains(@class, "single-location")]',
            ),
            callback="parse",
        )
    ]

    def parse(self, response):
        properties = {
            "ref": response.url.split("/")[-1],
            "addr_full": ", ".join(
                filter(None, map(str.strip, response.xpath('//span[@class="loc-add"]//text()').getall()))
            ),
            "phone": response.xpath('//span[@class="loc-ph"]/text()').get().strip(),
            "website": response.url,
        }
        extract_google_position(properties, response)

        days_list = response.xpath('//div[contains(@class, "hours-list")][1]//li/text()').getall()
        hours_list = response.xpath('//div[contains(@class, "hours-list")][2]//li/text()').getall()
        hours_string = " ".join(["{}: {}".format(x[0], x[1]) for x in zip(days_list, hours_list)])
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)

        yield Feature(**properties)
