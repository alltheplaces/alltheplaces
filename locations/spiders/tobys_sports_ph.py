import re

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class TobysSportsPHSpider(Spider):
    name = "tobys_sports_ph"
    item_attributes = {"brand": "Toby's Sports", "brand_wikidata": "Q117747741"}
    start_urls = ["https://www.tobys.com/pages/find-store"]
    no_refs = True
    STORE_DETAILS_RE = re.compile(
        r"""
           Landline:\s*(?P<phone>.*?)
           \s*Address:\s*(?P<address>.*?)
           \s*Store\s+Hours:\s*(?P<hours>.*)
           """,
        re.IGNORECASE | re.DOTALL | re.VERBOSE,
    )

    def parse(self, response: Response):
        for store in response.xpath('//*[@class="disclosure disclosure--row"]'):
            item = Feature()
            item["name"] = store.xpath("normalize-space(.//summary//h4)").get()

            details = " ".join(
                text.strip()
                for text in store.xpath('.//div[contains(@class, "disclosure__content")]//text()').getall()
                if text.strip()
            )

            match = self.STORE_DETAILS_RE.search(details)
            if match:
                item["phone"] = match.group("phone").strip(" \"'")
                item["addr_full"] = match.group("address").strip(" \"'")

                hours = match.group("hours").strip()
                if hours:
                    try:
                        opening_hours = OpeningHours()
                        opening_hours.add_ranges_from_string(hours)
                        item["opening_hours"] = opening_hours
                    except (ValueError, TypeError):
                        pass

            apply_category(Categories.SHOP_SPORTS, item)
            yield item
            # apply_category(Categories.SHOP_SPORTS, item)
            #
            # yield item


#             item["phone"] = store.xpath(
# 'normalize-space(.//strong[contains(.,"Landline")]/following-sibling::text()[1])'
# ).get()
#             item["addr_full"] = store.xpath(
# 'normalize-space(.//strong[contains(.,"Address")]/following-sibling::text()[1])'
# ).get(),
#             apply_category(Categories.SHOP_SPORTS, item)
#             try:
#                 oh = OpeningHours()
#                 oh.add_ranges_from_string(''.join(store.xpath('.//strong[contains(.,"Store Hours")]/following-sibling::text()').getall()).strip().strip())
#                 item["opening_hours"] = oh
#             except:
#                 pass
#             yield item
#
