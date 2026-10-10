import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The site lists its restaurants on a page per state, each holding a block per
# restaurant with the city, address, phone and the franchisee's own website.
#
# The state pages come from the sitemap. Addresses spell the state out on some
# blocks and abbreviate it on others.
#
# No coordinates are published: the map links are goo.gl short links. No
# opening hours are published either.


class OriginalPancakeHouseUSSpider(SitemapSpider):
    name = "original_pancake_house_us"
    item_attributes = {"brand": "The Original Pancake House", "brand_wikidata": "Q7755384"}
    allowed_domains = ["originalpancakehouse.com", "www.originalpancakehouse.com"]
    sitemap_urls = ["https://originalpancakehouse.com/sitemap.xml"]
    sitemap_rules = [(r"/phloc_([a-z]{2})\.html$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        state = response.url.rsplit("_", 1)[-1].removesuffix(".html").upper()

        for location in response.xpath('//div[@class="location"]'):
            lines = [
                re.sub(r"\s+", " ", line).strip() for line in location.xpath("./p[1]//text()").getall() if line.strip()
            ]
            # "Arlington Heights, Illinois 60004", or with the state abbreviated.
            if not lines or not (locality := re.fullmatch(r"(.+?),\s*([A-Za-z .]+?)\s+(\d{5})", lines[-1])):
                continue

            item = Feature()
            item["branch"] = re.sub(r"\s+", " ", location.xpath("string(./h3)").get("")).strip() or None
            item["street_address"] = merge_address_lines(lines[:-1])
            item["city"], _, item["postcode"] = [part.strip() for part in locality.groups()]
            item["state"] = state
            item["ref"] = f"{state}-{item['branch']}"
            item["phone"] = location.xpath('.//li[contains(text(), "Phone")]/text()').re_first(r"Phone:\s*(.+)")
            item["website"] = location.xpath('.//li[contains(text(), "Website")]/a/@href').get()

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "breakfast;pancake"

            yield item
