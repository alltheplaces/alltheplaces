import scrapy
from requests_cache import Response

from locations.categories import Categories, Extras, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class HSBCSpider(StructuredDataSpider):
    name = "hsbc_tw"
    item_attributes = {"brand": "HSBC", "brand_wikidata": "Q190464", "extras": Categories.BANK.value}
    start_urls = ["https://www.hsbc.com.tw/en-tw/ways-to-bank/branch/"]

    def parse(self, response: Response, **kwargs):
        for branch in response.xpath(r'//*[@class="desktop"]//td[2]').xpath("normalize-space()").getall():
            url = "https://www.hsbc.com.tw/en-tw/branch-list/" + branch.lower().replace(
                "taoyuan branch", "tahsin branch"
            ).replace(" (bilingual branch)", "").replace(" ", "-")
            yield scrapy.Request(url=url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        for service in ld_data["hasOfferCatalog"]["itemListElement"]:
            apply_yes_no(Extras.ATM, item, "atm" in service["itemOffered"]["name"].lower())
        yield item
