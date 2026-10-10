import re
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class DollarSelfStorageUSSpider(Spider):
    name = "dollar_self_storage_us"
    item_attributes = {"brand": "Dollar Self Storage", "name": "Dollar Self Storage"}
    start_urls = ["https://www.dollarselfstorage.com/storage-locations/index.php"]

    def parse(self, response: TextResponse, **kwargs) -> Iterable[Request]:
        for href in set(response.css("a::attr(href)").getall()):
            if re.fullmatch(r"/storage-locations/[a-z-]+/[a-z0-9-]+-self-storage\.php", href):
                yield response.follow(href, callback=self.parse_location)

    def parse_location(self, response: TextResponse, **kwargs) -> Iterable[Feature]:
        card = response.css(".d-learch").get() or ""
        lines = [line.strip() for line in response.css(".d-learch *::text").getall() if line.strip()]
        for i, line in enumerate(lines):
            if i > 0 and (match := re.fullmatch(r"(.+?),? ([A-Za-z ]+?),? (\d{5})", line)):
                break
        else:
            self.logger.warning("Unparseable address on %s", response.url)
            return

        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["street_address"] = lines[i - 1]
        item["city"], state, item["postcode"] = match.groups()
        if len(state) == 2:
            item["state"] = state
        item["phone"] = response.css('.d-learch a[href^="tel:"] *::text').get()
        item["email"] = response.css('.d-learch a[href^="mailto:"]::attr(href)').get("").removeprefix("mailto:")
        item["branch"] = item["city"]
        if store_number := re.search(r"#(\d+)", card):
            item["extras"]["ref:dss"] = store_number.group(1)

        extract_google_position(item, response)

        office_hours = response.xpath('//div[@class="modal-body text-center"]/p[1]//text()').getall()
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(" ".join(office_hours).replace("Office:", ""))

        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
