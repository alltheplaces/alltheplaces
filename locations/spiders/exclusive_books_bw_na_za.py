from scrapy import Spider

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

state_country_map = {
    "botswana": {"country": "BW"},
    "eastern_cape": {"country": "ZA", "state": "Eastern Cape"},
    "freestate": {"country": "ZA", "state": "Free State"},
    "gauteng": {"country": "ZA", "state": "Gauteng"},
    "kwazulu_natal": {"country": "ZA", "state": "KwaZulu-Natal"},
    "mpumalanga": {"country": "ZA", "state": "Mpumalanga"},
    "namibia": {"country": "NA"},
    "western_cape": {"country": "ZA", "state": "Western Cape"},
}


class ExclusiveBooksBWNAZASpider(Spider):
    name = "exclusive_books_bw_na_za"
    item_attributes = {"brand": "Exclusive Books", "brand_wikidata": "Q5419679"}
    start_urls = ["https://exclusivebooks.co.za/pages/find-a-store"]
    no_refs = True

    def parse(self, response):
        for location in response.xpath('.//div[contains(@class, "region--block")]'):
            item = Feature()
            item["branch"] = location.xpath(".//h4/text()").get()
            address_lines = location.xpath('.//strong[contains(text(), "ADDRESS:")]/../p/text()').getall()
            item["addr_full"] = clean_address(address_lines)
            try:
                int(address_lines[-1])
                item["postcode"] = address_lines[-1]
            except ValueError:
                pass
            item["phone"] = location.xpath('.//a[contains(@href, "tel:")]/@href').get()
            item["email"] = location.xpath('.//a[contains(@href, "mailto:")]/@href').get()
            if match := state_country_map.get(location.xpath("@class").get().split("--block")[0]):
                item.update(match)
            else:
                self.crawler.stats.inc_value(
                    f"atp/{self.name}/failed_state_match/{location.xpath('@class').get().split('--block')[0]}"
                )
            yield item
