from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ComptoirLibanaisSpider(Spider):
    name = "comptoir_libanais"
    item_attributes = {"brand": "Comptoir Libanais", "brand_wikidata": "Q91025096"}
    start_urls = ["https://www.comptoirlibanais.com/locations/"]
    # The map embeds on these pages point somewhere else (Dubai is off the coast of
    # Qatar and Wigmore Street reuses South Kensington's), so skip their coordinates.
    wrong_maps = ["/locations/dubai/", "/locations/wigmore-street/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[contains(@class, "framed-tile")][.//h5]'):
            item = Feature()
            item["website"] = item["ref"] = location.xpath(".//a/@href").get()
            item["branch"] = location.xpath("normalize-space(.//h5)").get()
            item["addr_full"] = merge_address_lines(location.xpath("./p//text()").getall())
            item["phone"] = location.xpath('.//a[starts-with(@href, "tel:")]/@href').get("")
            yield response.follow(item["website"], callback=self.parse_location, cb_kwargs={"item": item})

    def parse_location(self, response: Response, item: Feature) -> Any:
        if not response.url.endswith(tuple(self.wrong_maps)):
            extract_google_position(item, response)

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            " ".join(response.xpath('//h3[text()="Hours"]/following-sibling::p//text()').getall()).replace(".", ":")
        )

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "lebanese"

        yield item
