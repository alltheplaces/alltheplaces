from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class DiscReplayUSSpider(CrawlSpider):
    name = "disc_replay_us"
    item_attributes = {"brand": "Disc Replay", "brand_wikidata": "Q108202431"}
    allowed_domains = ["www.discreplay.com"]
    start_urls = ["https://www.discreplay.com/locations-list/"]
    rules = [Rule(LinkExtractor(allow=r"/locations/.+"), callback="parse")]

    def parse(self, response):
        item = Feature()
        item["ref"] = response.url.rstrip("/").split("/")[-1]
        item["addr_full"] = response.css(".address::text").get()
        item["phone"] = response.css(".phone::attr(href)").get()
        item["website"] = response.url

        item["lon"] = response.css("#listing-map::attr(data-lng)").get()
        item["lat"] = response.css("#listing-map::attr(data-lat)").get()

        days_list = response.css(".day::text").getall()
        hours_list = response.css(".hours::text").getall()
        hours_string = " ".join([f"{x[0]}: {x[1]}" for x in zip(days_list, hours_list)])
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)

        apply_category(Categories.SHOP_VIDEO_GAMES, item)

        yield item
