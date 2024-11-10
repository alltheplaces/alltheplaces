import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.mapy_cz_url import extract_mapy_cz_position
from locations.structured_data_spider import extract_phone


class ManufakturaSpider(CrawlSpider):
    name = "manufaktura"
    allowed_domains = ["manufakturashop.com"]
    start_urls = ["https://manufakturashop.com/stores/"]
    rules = [Rule(LinkExtractor(allow=r"/stores/\d+"), callback="parse")]
    item_attributes = {
        "brand": "Manufaktura",
        "brand_wikidata": "Q107740958",
    }

    def parse(self, response):
        item = Feature()
        item["ref"] = response.url.split("/")[-1]
        item["website"] = response.url
        item["name"] = response.xpath("//h1/text()").get()
        address_lines = response.xpath("//p[@class='p-address']/text()").getall()
        item["street_address"] = address_lines[0].strip(",")  # strip trailing comma
        item["postcode"] = re.match(r"\d{3}\s?\d{2}", address_lines[1].strip())[0]
        item["city"] = address_lines[1].strip().removeprefix(item["postcode"]).strip()
        item["image"] = response.xpath("//*[@class='seller-gallery-item']/img/@src").get()
        extract_phone(item, response)
        extract_mapy_cz_position(item, response)
        apply_category(Categories.SHOP_COSMETICS, item)

        if item["email"].endswith(".cz"):
            item["country"] = "CZ"
        elif item["email"].endswith(".sk"):
            item["country"] = "SK"
        else:
            raise RuntimeError("Cannot detect country from email: {}".format(item["email"]))

        seller_info = response.xpath("//*[@class='seller-detail-info']").get()
        if "Wheelchair access" in seller_info:
            apply_yes_no(Extras.WHEELCHAIR, item, True)

        oh = OpeningHours()
        for row in response.xpath("//*[@class='seller-detail-info']//tr"):
            day, hrs = row.xpath("./td/text()").getall()
            oh.add_ranges_from_string(day.strip() + " " + hrs.strip(), DAYS_EN)
        item["opening_hours"] = oh

        yield item
