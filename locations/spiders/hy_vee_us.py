import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class HyVeeUSSpider(SitemapSpider):
    name = "hy_vee_us"
    item_attributes = {"brand": "Hy-Vee", "brand_wikidata": "Q1639719"}
    allowed_domains = ["www.hy-vee.com"]
    sitemap_urls = ["https://www.hy-vee.com/sitemap-locations.xml"]
    sitemap_rules = [(r"/stores/detail\.aspx\?s(c)?=\d+$", "parse")]
    custom_settings = {"REDIRECT_ENABLED": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        properties = Feature(
            ref=response.url.split("=", 1)[1],
            name=response.xpath('//div[@id="page_content"]/h1/text()').get().strip(),
            addr_full=merge_address_lines(
                response.xpath('//div[contains(strong/text(), "Address")]/text()[not(parent::a)]').getall()
            ),
            phone=response.xpath('//a[contains(@href, "tel:")]/@href').get("").replace("tel:", "").strip(),
            website=response.url,
        )

        if image_path := response.xpath('//img[@class="page_banner"]/@src').get():
            properties["image"] = image_path if "https://" in image_path else "https://www.hy-vee.com" + image_path

        if hours_raw := response.xpath('//div[@id="page_content"]/p[last()]/text()').get():
            oh = OpeningHours()
            oh.add_ranges_from_string(hours_raw.upper().replace("A.M.", "AM").replace("P.M.", "PM"))
            properties["opening_hours"] = oh

        apply_category(Categories.SHOP_SUPERMARKET, properties)

        if g := response.xpath("//a[contains(@href, 'q=place_id:')]/@href").get():
            properties["extras"]["ref:google:place_id"] = g.rsplit(":", 1)[1]

        yield properties
