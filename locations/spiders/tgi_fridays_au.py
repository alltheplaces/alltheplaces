from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import SocialMedia, set_social_media
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.tgi_fridays_us import TgiFridaysUSSpider
from locations.structured_data_spider import clean_facebook


class TgiFridaysAUSpider(Spider):
    name = "tgi_fridays_au"
    item_attributes = TgiFridaysUSSpider.item_attributes
    allowed_domains = ["www.tgifridays.com.au", "goo.gl"]
    start_urls = ["https://www.tgifridays.com.au/page-data/book/page-data.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Ignore www.google.com robots.txt

    def parse(self, response):
        for location in response.json()["result"]["pageContext"]["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["url"]
            item["addr_full"] = clean_address([location["address"]["line_1"], location["address"]["line_2"]])
            item["state"] = location["state"]
            item["website"] = "https://www.tgifridays.com.au/locations/{}/".format(location["url"])

            item["opening_hours"] = OpeningHours()
            for day_name, time_ranges in location["hours"].items():
                for time_range in time_ranges.values():
                    if not time_range["open"] or not time_range["close"]:
                        continue
                    item["opening_hours"].add_range(day_name.title(), time_range["open"], time_range["close"])

            facebook_account = clean_facebook(location["facebook_url"])
            set_social_media(item, SocialMedia.FACEBOOK, facebook_account)

            yield Request(url=location["map_address"], meta={"item": item}, callback=self.parse_maps_url)

    # Follow shortened URL to find full Google Maps URL containing coordinates
    def parse_maps_url(self, response):
        item = response.meta["item"]
        item["lat"], item["lon"] = url_to_coords(response.url)
        yield item
