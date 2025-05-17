from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class TheLearningExperienceUSSpider(SitemapSpider):
    name = "the_learning_experience_us"
    item_attributes = {"brand": "Learning Experience", "brand_wikidata": "Q29097682"}
    allowed_domains = ["thelearningexperience.com"]
    sitemap_urls = ["https://thelearningexperience.com/centers-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/thelearningexperience\.com\/centers\/.+", "parse")]
    download_delay = 0.2

    def parse(self, response: Response) -> Iterable[Feature]:
        if response.xpath('//p[@class="center-status"]/text()').get() == "Coming soon":
            return
        if response.xpath('//p[@class="center-register"]/text()').get() in ["Pre-Registration Now Open", "Tours Available"]:
            return
        properties = {
            "ref": response.url,
            "branch": response.xpath('//h1[@class="banner__title"]/span[1]/text()').get(),
            "addr_full": merge_address_lines(response.xpath('//div[@class="banner__left_contacts_item location"]/p[1]//text()').getall()),
            "phone": response.xpath('//div[@class="banner__left_contacts_item phone"]/a[1]/@href').get().removeprefix("tel:"),
            "email": response.xpath('//div[@class="banner__left_contacts_item mail"]/a[1]/@href').get().removeprefix("mailto:"),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        hours_text = response.xpath('//div[@class="banner__left_contacts_item time"]/p[1]/text()').get().replace("M-F", "Mon-Fri")
        properties["opening_hours"].add_ranges_from_string(hours_text)
        extract_google_position(properties, response)
        apply_category(Categories.KINDERGARTEN, properties)
        yield Feature(**properties)

