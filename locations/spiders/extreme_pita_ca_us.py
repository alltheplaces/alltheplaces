import re
from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class ExtremePitaCAUSSpider(Spider):
    name = "extreme_pita_ca_us"
    item_attributes = {
        "brand_wikidata": "Q5422367",
        "brand": "Extreme Pita",
    }
    allowed_domains = ["extremepita.com"]
    start_urls = ["https://extremepita.com/locations/"]
    seen_refs: set[str] = set()

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for card in response.xpath('//div[contains(@class, "e-loop-item")]'):
            ref = card.xpath("./@class").re_first(r"post-(\d+)")
            if not ref or ref in self.seen_refs:
                continue
            self.seen_refs.add(ref)

            headings = card.xpath('.//*[contains(@class, "elementor-heading-title")]//text()').getall()
            headings = [h.strip() for h in headings if h.strip()]

            item = Feature()
            item["ref"] = ref
            if headings:
                item["branch"] = headings[0]
            if len(headings) > 1:
                item["addr_full"] = re.sub(r"\s+", " ", headings[1])
            item["phone"] = card.xpath('.//*[contains(@class, "elementor-icon-list-text")]//text()').get()

            if match := re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", card.get()):
                item["lat"], item["lon"] = match.groups()

            apply_category(Categories.FAST_FOOD, item)
            yield item

        for next_page in response.xpath('//a[contains(@href, "/locations/page/")]/@href').getall():
            yield response.follow(urljoin(response.url, next_page), callback=self.parse)
