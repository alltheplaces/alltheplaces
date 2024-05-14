import re

from scrapy import Request

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class ProvidenceUSSpider(StructuredDataSpider):
    name = "providence_us"
    item_attributes = {"brand": "Providence", "brand_wikidata": "Q7252430"}
    allowed_domains = ["www.providence.org"]
    start_urls = ["https://www.providence.org/locations?postal=66102&latlng=39.103,-94.666&radius=100000&page=1"]
    wanted_types = ["MedicalOrganization", "MedicalClinic", "Hospital"]

    def parse(self, response):
        self.parse_location_results(response)
        pager_script = response.xpath('//script[contains(text(), "dig.modules.paging(")]/text()').get()
        if total_pages_search_result := re.search(
            r"\", (\d+), \d+, \"__locationSearchGetPageRequest\"\);", pager_script
        ):
            total_pages = int(total_pages_search_result.group(1))
        else:
            return
        for page_number in range(2, total_pages, 1):
            yield Request(url=response.url[:-1] + str(page_number), callback=self.parse_location_results)

    def parse_location_results(self, response):
        location_urls = response.xpath('//div[@class="location-card-title"]/h2/a/@href').getall()
        for location_url in location_urls:
            yield Request(url=f"https://www.providence.org{location_url}", callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data):
        item["facebook"] = None
        item["twitter"] = None
        item["image"] = None
        item["opening_hours"] = OpeningHours()
        hours_string = " ".join(
            filter(
                None,
                response.xpath(
                    '//div[contains(@class, "location-detail")][1]/div[contains(@class, "hours-text")]//text()'
                ).getall(),
            )
        )
        hours_string = (
            hours_string.strip()
            .replace(";", ":")
            .replace("a.m.", "AM")
            .replace("a.m", "AM")
            .replace("p.m.", "PM")
            .replace("p.m", "PM")
        )
        item["opening_hours"].add_ranges_from_string(hours_string)
        if ld_data["@type"] == "Hospital":
            apply_category(Categories.HOSPITAL, item)
        elif ld_data["@type"] == "MedicalClinic" or ld_data["@type"] == "MedicalOrganization":
            apply_category(Categories.CLINIC, item)
        yield item
