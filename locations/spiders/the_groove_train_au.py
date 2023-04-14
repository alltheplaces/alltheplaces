import re

from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class TheGrooveTrainAUSpider(SitemapSpider):
    name = "the_groove_train_au"
    item_attributes = {"brand": "The Groove Train", "brand_wikidata": "Q117710890"}
    allowed_domains = ["groovetrain.com.au"]
    sitemap_urls = ["https://groovetrain.com.au/location-sitemap.xml"]
    sitemap_rules = [(r"\/location\/([\w\-]+)\/", "parse")]

    def parse(self, response):
        location_box = response.xpath('//div[contains(@class, "location-box")]/section')
        properties = {
            "ref": re.search(self.sitemap_rules[0][0], response.url).group(1),
            "name": location_box.xpath('//div[contains(@class, "big-title")]/div/text()').get().strip(),
            "state": location_box.xpath('//div[contains(@class, "parent")]/text()').get().strip(),
            "addr_full": location_box.xpath('//div[contains(@class, "location")]/div[2]/text()').get().strip(),
            "phone": location_box.xpath(
                '//div[contains(@class, "button-bar")]/div[contains(@class, "row1")]//p//text()'
            )
            .get()
            .strip(),
            "website": response.url,
        }
        extract_google_position(properties, response)
        hours_string = " ".join(
            filter(
                None,
                location_box.xpath(
                    '//div[contains(@class, "trading-hours")]/div[contains(@class, "text")]/text()'
                ).getall(),
            )
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
