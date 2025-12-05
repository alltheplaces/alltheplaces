from typing import Any, AsyncIterator

from scrapy import Selector, Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class FultonBankUSSpider(Spider):
    name = "fulton_bank_us"
    item_attributes = {"brand": "Fulton Bank", "brand_wikidata": "Q16976594"}

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://www.fultonbank.com/api/Branches/Search",
            formdata={
                "QueryModel.SearchTerm": "kansas",
                "QueryModel.MaxResults": "1000",
            },  # center location
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        branch_popups = Selector(text=response.json()["branchFlyouts"])  # contains extra info

        for location in Selector(text=response.json()["branchResults"]).xpath("//*[@data-lat]"):
            item = Feature()
            item["ref"] = location.xpath("./@data-id").get()
            item["lat"] = location.xpath("./@data-lat").get()
            item["lon"] = location.xpath("./@data-long").get()
            item["branch"] = location.xpath("./@data-name").get()
            item["addr_full"] = clean_address(location.xpath('.//*[@class="location-address"]/text()').get(""))

            # Use data-id to extract phone, opening hours etc. from branch_popups
            location_details = branch_popups.xpath(f'.//*[@data-id="{item["ref"]}"]')
            item["phone"] = location_details.xpath('.//a[contains(@href, "tel:")]/@href').get()

            opening_hours = location_details.xpath(
                './/*[@class="info-title"][contains(text(), "Lobby Hours") or contains(text(), "Window Hours")]//following-sibling::*[@class="hours-extended"]//*[@class="hours-row"]/text()'
            ).getall()
            item["opening_hours"] = self.parse_opening_hours(opening_hours)

            services = location_details.xpath(
                './/*[@class="info-block available-services"]//*[@class="info-text"]/text()'
            ).get("")

            if "ATM Only" in location_details.get(""):
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, "ATM" in services)
                apply_yes_no(Extras.CASH_IN, item, "ATM Accepts Deposits" in services)
                apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in services)
            yield item

    def parse_opening_hours(self, opening_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            if "Closed" in rule.title():
                oh.set_closed(rule.title().replace("Closed", ""))
            else:
                oh.add_ranges_from_string(rule)
        return oh
