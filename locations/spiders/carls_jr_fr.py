from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.carls_jr_us import CarlsJrUSSpider


class CarlsJrFRSpider(CrawlSpider):
    name = "carls_jr_fr"
    item_attributes = CarlsJrUSSpider.item_attributes
    allowed_domains = ["www.carlsjr.fr"]
    start_urls = ["https://www.carlsjr.fr/nos-restaurants"]
    rules = [Rule(LinkExtractor(allow=r"/carls-"), callback="parse")]

    def parse(self, response):
        properties = {
            "ref": response.url.split("/")[-1],
            "website": response.url,
            "branch": response.xpath("//title/text()").get("").split("|")[0].strip(),
        }

        if contact_box := response.xpath(
            '//div[contains(@class, "wixui-rich-text") and .//p[contains(string(.), "Tel:")]]'
        ):
            raw_text = contact_box.xpath("string(.)").get()
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

            for i, line in enumerate(lines):
                if "Tel:" in line:
                    properties["phone"] = line.replace("Tel:", "").strip()

                    addr_lines = lines[:i]
                    if addr_lines:
                        addr_lines.pop(0)

                    properties["addr_full"] = merge_address_lines(addr_lines)
                    break

        apply_category(Categories.FAST_FOOD, properties)
        yield Feature(**properties)
