from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class HobbytownUSSpider(SitemapSpider, PlaywrightSpider):
    name = "hobbytown_us"
    item_attributes = {"brand": "HobbyTown", "brand_wikidata": "Q5874921"}
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    sitemap_urls = ["https://www.hobbytown.com/sitemapindex.xml"]
    sitemap_rules = [(r"https://www.hobbytown.com/[^/]+/[^/]+", "parse")]
    sitemap_follow = ["locations"]

    def parse(self, response: TextResponse):
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get().removeprefix("HobbyTown ")
        item["street_address"] = response.xpath('//*[@class="col-12 location-contact"]//p//text()[1]').get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath('//*[@class="col-12 location-contact"]//p//text()[2]').get()]
        )
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]//text()').get()
        item["website"] = item["ref"] = response.url
        extract_google_position(item, response)
        try:
            oh = OpeningHours()
            for day_time in response.xpath('//*[@class="week-day"]'):
                day = day_time.xpath('.//*[@class="col-4 col-md-12 day"]/text()').get()
                open_time = day_time.xpath('.//*[@class="col-8 col-md-12 hours"]/span[1]/text()').get()
                close_time = day_time.xpath('.//*[@class="col-8 col-md-12 hours"]/span[3]/text()').get()
                oh.add_range(day, open_time, close_time, "%I:%M %p")
            item["opening_hours"] = oh
        except:
            pass
        apply_category(Categories.SHOP_CRAFT, item)
        yield item
