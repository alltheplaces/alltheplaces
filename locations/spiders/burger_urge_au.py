from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class BurgerUrgeAUSpider(SitemapSpider):
    name = "burger_urge_au"
    item_attributes = {"brand": "Burger Urge", "brand_wikidata": "Q19589751"}
    allowed_domains = ["burgerurge.com.au"]
    sitemap_urls = ["https://burgerurge.com.au/location-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/burgerurge\.com\.au\/location\/[\w\-]+\/$", "parse")]

    def parse(self, response):
        properties = {
            "ref": response.xpath('//div[contains(@class, "button-pickup")]/a/@href')
            .get()
            .split("location=", 1)[1]
            .split("&", 1)[0],
            "name": response.xpath('//a[contains(@class, "storename")]/text()').get(),
            "addr_full": " ".join(
                filter(None, map(str.strip, response.xpath('//div[contains(@class, "address-loc")]//text()').getall()))
            ),
            "phone": response.xpath('//li[@class="our-details"]/a[contains(@href, "tel:")]/@href')
            .get()
            .replace("tel:", ""),
            "website": response.url,
        }
        extract_google_position(properties, response)
        hours_string = " ".join(
            filter(
                None,
                map(
                    str.strip, response.xpath('//ul[contains(@class, "our-details")]/li[not(@class)]//text()').getall()
                ),
            )
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
