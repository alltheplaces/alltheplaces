import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class IndependentFinancialUSSpider(scrapy.Spider):
    name = "independent_financial_us"
    item_attributes = {"brand": "Independent Financial", "brand_wikidata": "Q6016398"}
    start_urls = ["https://www.independentbank.com/find-a-location/"]

    def parse(self, response: Response, **kwargs):
        for location in response.xpath('//*[@class="locations-listings"]//article'):
            item = Feature()
            item["branch"] = location.xpath(".//@aria-label").get()
            item["name"] = self.item_attributes["brand"]
            item["ref"] = location.xpath(".//@id").get()
            item["lat"] = location.xpath(".//@data-lat").get()
            item["lon"] = location.xpath(".//@data-lng").get()
            item["addr_full"] = location.xpath(".//@data-address").get()
            location_type = (
                location.xpath('.//*[@class="location-item__options options"]/span').xpath("normalize-space()").getall()
            )
            if "Bank" in location_type:
                apply_category(
                    Categories.BANK,
                    item,
                )
                apply_yes_no(Extras.ATM, item, ("ATM" in location_type))
            elif location_type in [["ATM"], ["Drive Up"]]:
                apply_category(Categories.ATM, item)
            elif location_type in [["Mortgage & Loan Center"], ["Commercial Loan Center"]]:
                apply_category(Categories.OFFICE_FINANCIAL, item)
            yield item
