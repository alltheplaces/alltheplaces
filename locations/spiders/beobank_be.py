from typing import AsyncIterator

from scrapy import Selector
from scrapy.http import FormRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class BeobankBESpider(StructuredDataSpider):
    name = "beobank_be"
    item_attributes = {"brand": "Beobank", "brand_wikidata": "Q14911971"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[FormRequest]:
        headers = {
            "Accept": "text/json; charset=utf-8, text/xml; charset=utf-8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.beobank.be",
            "Referer": "https://www.beobank.be/nl/resultaat-kantoren.html?search=bruges&amp;selectedServicesValues=1&amp;selectedMarketTypeValues=0&amp;selectedOpeningDaysValues=0&amp;selectedPoiTypeValue=2",
            "x-TargetApplicationBlockId": "C",
        }

        for type in ["1", "2"]:
            formdata = {
                "Data_SelectedPoiTypeValue": type,
                "Bool:Data_SearchListOpeningDay_CheckBoxListItemViewModel_Checked": "false",
                "Bool:Data_SearchListOpeningDay_CheckBoxListItemViewModel_2__Checked": "false",
                "Bool:Data_SearchListOpeningDay_CheckBoxListItemViewModel_3__Checked": "false",
                "[t:xsd%3astring;]Data_Search": "bruges",
                "_FID_DoLoadMoreResults": "",
                "Data_SearchListOpeningDaySelectedItemsCount": "0",
                "Data_CurrentPageIndex": "31",
                "Data_IsSearchDone": "true",
                "_wxf2_pseq": "32",
                "_wxf2_pmode": "Normal",
                "_wxf2_ptarget": "C:P:up",
            }

            yield FormRequest(
                url="https://www.beobank.be/nl/resultaat-kantoren.html?_tabi=C&_pid=SearchResults&k_search=bruges&k_selectedServicesValues=1&k_selectedMarketTypeValues=0&k_selectedOpeningDaysValues=0&k_selectedPoiTypeValue=2",
                formdata=formdata,
                headers=headers,
                method="POST",
                cb_kwargs={"location_type": type},
                callback=self.parse,
            )

    def parse(self, response, **kwargs):
        raw_data = Selector(text=response.json()["HtmlContent"]["C:P:up"])
        if kwargs["location_type"] == "2":
            for location in raw_data.xpath("//ul//li"):
                item = Feature()
                if "BEOBANK" in location.xpath(".//a/text()").get():
                    item["branch"] = location.xpath(".//a/text()").get()
                    item["ref"] = location.xpath(".//@id").get()
                    item["street_address"] = location.xpath(".//p/text()").get()
                    item["addr_full"] = merge_address_lines(
                        [item["street_address"], location.xpath(".//p/text()[2]").get()]
                    )
                    apply_category(Categories.ATM, item)
                    yield item
        if kwargs["location_type"] == "1":
            for location in raw_data.xpath("//ul//li"):
                link = location.xpath(".//@href").get()
                yield Request(url=link, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.BANK, item)
        yield item
