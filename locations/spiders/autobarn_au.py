import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AutobarnAUSpider(SitemapSpider):
    name = "autobarn_au"
    item_attributes = {"brand": "Autobarn", "brand_wikidata": "Q105831666"}
    allowed_domains = ["autobarn.com.au"]
    sitemap_urls = ["https://autobarn.com.au/ab/sitemap/store/store-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/autobarn\.com\.au\/ab\/store\/\d{2}[A-Z]{2}$", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        properties = {
            "ref": response.url.split("/")[-1],
            "branch": response.xpath("//main/div[1]/div[1]/h3/text()").get(),
            "addr_full": merge_address_lines(
                response.xpath("//main/div[1]/div[1]/div[2]/div[1]/div[3]/p/text()").getall()
            ),
            "phone": response.xpath('//main/div[1]/div[1]/div[2]/div[1]//a[contains(@href, "tel:")]/@href')
                .get()
                .removeprefix("tel:"),
            "email": response.xpath('//main/div[1]/div[1]/div[2]/div[1]//a[contains(@href, "mailto:")]/@href')
                .get()
                .removeprefix("mailto:"),
            "website": response.url,
            "image": response.xpath("//main/div[1]/div[1]/div[2]/div[1]/div[2]/img/@src").get(),
            "opening_hours": OpeningHours(),
        }

        extract_google_position(properties, response)

        hours_text = re.sub(
            r"\s+", " ", " ".join(response.xpath("//main/div[1]/div[1]/div[2]/div[1]/div[5]/div//text()").getall())
        )
        properties["opening_hours"].add_ranges_from_string(hours_text)

        apply_category(Categories.SHOP_CAR_PARTS, properties)

        yield Feature(**properties)
