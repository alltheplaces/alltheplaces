import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations are listed in an accordion on the home page, each block giving
# the shop's name, a "street, city, state postcode" line and a phone.
#
# The accordion is rendered twice, once for each layout, so records are keyed
# on their name and address. Shops that have not opened are listed as
# "COMING SOON!" with no address and are skipped.
#
# No coordinates are published: the address links are Google short links.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})")


class BetterBlendUSSpider(Spider):
    name = "better_blend_us"
    item_attributes = {"brand": "Better Blend"}
    allowed_domains = ["www.betterblend-smoothies-bowls.com"]
    start_urls = ["https://www.betterblend-smoothies-bowls.com/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        seen = set()

        for block in response.xpath('//div[@data-grab="accordion-item-desc-text"]'):
            location = None

            for paragraph in block.xpath("./p"):
                text = re.sub(r"\s+", " ", " ".join(paragraph.xpath(".//text()").getall())).strip()
                if not text:
                    continue

                if text.lower().startswith("better blend"):
                    location = {"name": text, "page": paragraph.xpath('.//a[starts-with(@href, "/")]/@href').get()}
                    continue
                if not location or not (address := ADDRESS.fullmatch(text)):
                    continue

                item = Feature()
                item["street_address"], item["city"], item["state"], item["postcode"] = address.groups()
                # "Better Blend - Fort Mitchell"
                item["branch"] = location["name"].split(" - ", 1)[-1].strip()
                item["ref"] = re.sub(r"[^a-z0-9]+", "-", f"{item['branch']} {item['postcode']}".lower()).strip("-")
                if item["ref"] in seen:
                    location = None
                    continue
                seen.add(item["ref"])

                if page := location["page"]:
                    item["website"] = response.urljoin(page)
                if phone := block.xpath('.//a[starts-with(@href, "tel:")]/@href').re_first(r"tel:(.+)"):
                    item["phone"] = phone

                apply_category(Categories.FAST_FOOD, item)
                item["extras"]["cuisine"] = "smoothie;juice"

                location = None
                yield item
