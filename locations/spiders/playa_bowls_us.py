from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class PlayaBowlsUSSpider(CrawlSpider):
    name = "playa_bowls_us"
    item_attributes = {"brand": "Playa Bowls", "brand_wikidata": "Q114618507"}
    start_urls = ["https://playabowls.com/locations"]
    rules = [Rule(LinkExtractor("/location/"), callback="parse_store")]

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url.split("/")[-1]
        item["website"] = response.url

        address_text_list = response.css("div.elementor-widget-heading .elementor-heading-title::text").getall()
        address_text_list = [t.replace("\xa0", "").strip(", ") for t in address_text_list]
        item["branch"] = address_text_list[0]
        item["street_address"] = address_text_list[1]
        item["city"] = address_text_list[2]
        item["state"] = address_text_list[3]
        item["postcode"] = address_text_list[4]

        phone_link = response.css('a[href^="tel:"]::attr(href)').get()
        item["phone"] = phone_link.split(":")[1].replace("%20", " ")

        extract_google_position(item, response)
        apply_category(Categories.FAST_FOOD, item)

        yield item
