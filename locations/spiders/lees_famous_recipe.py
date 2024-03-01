import re

from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class LeesFamousRecipeSpider(SitemapSpider):
    name = "lees_famous_recipe"
    item_attributes = {"brand": "Lee's Famous Recipe Chicken", "brand_wikidata": "Q6512810"}
    allowed_domains = ["www.leesfamousrecipe.com"]
    sitemap_urls = ["https://www.leesfamousrecipe.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/.+/.+$", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["phone"] = response.xpath('//div[@class="tel"]/text()').get()
        item["name"] = "".join(response.xpath('//h1[@class="node-title"]//text()').getall())
        item["street_address"] = response.xpath('//div[@class="street-address"]/text()').get()
        item["city"] = response.xpath('//span[@class="locality"]/text()').get()
        item["state"] = response.xpath('//span[@class="region"]/text()').get()
        item["postcode"] = response.xpath('//span[@class="postal-code"]/text()').get()

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//div[@class="group-hours"]//p/text()').getall():
            if m := re.search(r"(\w+): (\d+:\d\d [ap]m) - (\d+:\d\d [ap]m)", rule):
                item["opening_hours"].add_range(m.group(1), m.group(2), m.group(3), time_format="%I:%M %p")

        apply_yes_no(Extras.DRIVE_THROUGH, item, response.xpath('//li[@class="drive-thru"]').get())

        extract_google_position(item, response)

        yield item
