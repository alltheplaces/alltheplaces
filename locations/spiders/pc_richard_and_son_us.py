import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class PcRichardAndSonUSSpider(Spider):
    name = "pc_richard_and_son_us"
    item_attributes = {"brand": "P. C. Richard & Son", "brand_wikidata": "Q7117161", "country": "US"}
    allowed_domains = ["www.pcrichard.com"]
    start_urls = ["https://www.pcrichard.com/store-locator/?isForm=true&showMap=true"]

    def parse(self, response):
        links = response.xpath("//a[contains(normalize-space(.), 'P.C. Richard and Son at ')]")
        if not links:
            raise ValueError("Store links missing from P.C. Richard & Son locator")

        for link in links:
            url = response.urljoin(link.attrib["href"])
            if "/stores/" not in url:
                continue
            label = link.xpath("normalize-space(.)").get()
            match = re.fullmatch(
                r"P\.C\. Richard and Son at (.+), ([^,]+), ([A-Z]{2}) (\d{5}(?:-\d{4})?)",
                label,
            )
            if not match:
                self.logger.warning("Unrecognized store address: %s", label)
                continue

            street, city, state, postcode = match.groups()
            item = Feature(
                ref=url,
                street_address=street,
                city=city,
                state=state,
                postcode=postcode,
                website=url,
            )
            apply_category(Categories.SHOP_ELECTRONICS, item)
            yield item
