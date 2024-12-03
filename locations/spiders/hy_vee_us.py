import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class HyVeeUSSpider(CrawlSpider):
    name = "hy_vee_us"
    item_attributes = {"brand": "Hy-Vee", "brand_wikidata": "Q1639719", "country": "US"}
    allowed_domains = ["www.hy-vee.com"]
    start_urls = ["https://www.hy-vee.com/aisles-online/stores"]
    rules = [Rule(LinkExtractor(allow=r"^https:\/\/www\.hy-vee\.com\/stores\/detail\.aspx\?sc=\d+$"), callback="parse")]
    # Some location pages were observed to redirect back to the location list page.
    custom_settings = {"REDIRECT_ENABLED": False}

    def parse(self, response):
        properties = {
            "ref": response.url.split("=", 1)[1],
            "name": response.xpath('//div[@id="page_content"]/h1/text()').get().strip(),
            "addr_full": re.sub(
                r"\s+", " ", " ".join(response.xpath('//div[@id="page_content"]/div[2]/div[1]/text()').getall())
            ).strip(),
            "phone": response.xpath('//div[@id="page_content"]/div[2]/div[2]/a[contains(@href, "tel:")]/@href')
            .get()
            .replace("tel:", ""),
            "website": response.url,
        }

        image_path = response.xpath('//img[@class="page_banner"]/@src').get()
        if image_path:
            if "https://" in image_path:
                properties["image"] = image_path
            else:
                properties["image"] = "https://www.hy-vee.com" + image_path

        hours_string = (
            re.sub(r"\s+", " ", " ".join(response.xpath('//div[@id="page_content"]/p[2]/text()').getall()))
            .upper()
            .replace("OPEN DAILY,", "Mon-Sun:")
            .replace("A.M.", "AM")
            .replace("P.M.", "PM")
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)

        apply_category(Categories.SHOP_SUPERMARKET, properties)

        yield Feature(**properties)
