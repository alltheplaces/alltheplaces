from urllib.parse import urlparse

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class PlsUsSpider(StructuredDataSpider):
    name = "pls_us"
    allowed_domains = ["pls247.com"]
    item_attributes = {
        "brand": "PLS Financial Services",
        "brand_wikidata": "Q126717580",
        "extras": Categories.SHOP_MONEY_LENDER.value,
    }
    start_urls = [
        f"https://pls247.com/{state}/elements/content_boxes/stores_ajax.html"
        for state in ["az", "ca", "il", "in", "ky", "ma", "ny", "nc", "oh", "ok", "tx", "wi"]
    ]
    search_for_facebook = False
    search_for_image = False
    time_format = "%I:%M %p"

    def pre_process_data(self, ld_data):
        for i, hr in enumerate(ld_data.get("openingHours", [])):
            ld_data["openingHours"][i] = hr.replace("—", "-")

    def parse(self, response):
        for link in response.xpath("//a[@class='row-i']/@href").getall():
            yield response.follow(link, callback=self.parse_sd)

        if next_url := response.xpath("//span[text()='Next']/../@href").get():
            yield response.follow(next_url)

    def post_process_item(self, item, response, ld_data):
        item["state"] = urlparse(response.url).path.split("/")[1].upper()
        yield item
