import re
from urllib.parse import quote, urljoin

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class PutkaPLSpider(CrawlSpider):
    name = "putka_pl"
    item_attributes = {"brand": "Putka", "brand_wikidata": "Q113093586"}
    start_urls = ["https://www.putka.pl/sklepy-firmowe"]
    rules = [
        Rule(LinkExtractor(r"/sklepy-firmowe/\d+$")),
        Rule(LinkExtractor(r"/sklepy-firmowe/\d+/\d+/$")),
        Rule(LinkExtractor(r"/sklepy-firmowe/\d+/\d+/(\d+)$"), "parse_store"),
    ]

    def parse_store(self, response, **kwargs):
        store_details = response.xpath("//div[contains(@class, 'sklep-details')]")
        street_address, post_code_city, phone = store_details.xpath("//table/tr[2]/td/text()").getall()
        post_code = post_code_city.split(" ")[0].strip()
        city = " ".join(post_code_city.strip().split(" ")[1:])
        phone = phone.strip().removeprefix("tel: ")
        image_path = store_details.xpath("//img[contains(@src, 'upload/sklepy')]/@src").get()
        opening_hours = OpeningHours()
        opening_hours_texts = store_details.xpath("//tr[5]/td/text()").getall()
        half_opening_hours_len = len(opening_hours_texts) // 2
        for i in range(half_opening_hours_len):
            opening_hours_text = (
                opening_hours_texts[i].strip().replace(".", "")
                + ": "
                + opening_hours_texts[half_opening_hours_len + i].strip()
            )
            opening_hours.add_ranges_from_string(ranges_string=opening_hours_text, days=DAYS_PL)
        properties = {
            "street_address": street_address.strip(),
            "city": city,
            "phone": phone,
            "postcode": post_code,
            "opening_hours": opening_hours,
        }
        if image_path:
            properties["image"] = urljoin("https://www.putka.pl/", quote(image_path))
        properties.update(kwargs)
        item = Feature(**properties)

        item["website"] = response.url
        item["ref"] = response.url.rsplit("/", 1)[1]

        if m := re.search(r"LatLng\((-?\d+\.\d+), (-?\d+\.\d+)\)", response.text):
            item["lat"], item["lon"] = m.groups()

        apply_category(Categories.SHOP_BAKERY, item)
        yield item
