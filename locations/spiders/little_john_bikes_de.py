import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class LittleJohnBikesDESpider(SitemapSpider):
    name = "little_john_bikes_de"
    item_attributes = {"brand": "Little John Bikes", "brand_wikidata": "Q99976320"}
    allowed_domains = ["littlejohnbikes.de"]
    sitemap_urls = ["https://littlejohnbikes.de/sitemap/filialen.xml"]
    sitemap_rules = [(r"^https:\/\/littlejohnbikes\.de\/filialen\/[^\/]+$", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        properties = {
            "branch": response.xpath("//h1/text()")
            .get()
            .removeprefix("Fahrradladen in ")
            .removeprefix("Dein Fahrradladen in "),
            "addr_full": merge_address_lines(
                response.xpath('//p[text()="Adresse"]/following-sibling::p/span/text()').getall()
            ),
            "phone": response.xpath('//span[text()="Telefon"]/following-sibling::span/text()').get(),
            "email": response.xpath('//p[text()="Mail"]/following-sibling::a/@href').get().removeprefix("mailto:"),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        properties["ref"] = properties["email"].split("@", 1)[0]
        hours_text = re.sub(
            r"\s+",
            " ",
            " ".join(response.xpath('//div[contains(@class, "mt-n-xs")]//text()').getall()).replace("Uhr", ""),
        )
        properties["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_DE)
        apply_category(Categories.SHOP_BICYCLE, properties)
        yield Feature(**properties)
