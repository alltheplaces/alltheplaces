import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class UwCreditUnionUSSpider(SitemapSpider):
    name = "uw_credit_union_us"
    item_attributes = {
        "brand": "UW Credit Union",
        "brand_wikidata": "Q7876156",
    }
    sitemap_urls = ["https://www.uwcu.org/sitemap.xml"]
    sitemap_rules = [(r"/branches-and-atms/(?!find-an-atm$)[^/]+$", "parse")]

    def parse(self, response: Response):
        address_p = response.xpath('//h2[text()="Address"]/following-sibling::p[1]')
        lines = [line.strip() for line in address_p.xpath(".//text()").getall() if line.strip()]
        if not lines:
            return

        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = re.sub(r"\s*Branch\s*$", "", response.xpath("//h1/text()").get("").strip())
        if len(lines) > 1 and (m := re.match(r"(.+),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)$", lines[-1])):
            item["street_address"] = merge_address_lines(lines[:-1])
            item["city"], item["state"], item["postcode"] = m.group(1), m.group(2), m.group(3)
            item["country"] = "US"
        else:
            item["street_address"] = merge_address_lines(lines)

        extract_google_position(item, response)

        if hours_text := self.extract_hours_block(response, "Lobby Hours"):
            oh = OpeningHours()
            oh.add_ranges_from_string(hours_text)
            item["opening_hours"] = oh

        if drive_up_text := self.extract_hours_block(response, "Drive Up Hours"):
            oh = OpeningHours()
            oh.add_ranges_from_string(drive_up_text)
            if oh.as_opening_hours():
                item["extras"]["opening_hours:drive_through"] = oh.as_opening_hours()

        apply_category(Categories.BANK, item)

        yield item

    @staticmethod
    def extract_hours_block(response: Response, heading: str) -> str:
        p = response.xpath(f'//h3[text()="{heading}"]/following-sibling::p[1]')
        lines = [line.strip() for line in p.xpath(".//text()").getall() if line.strip()]
        return "\n".join(lines)
