import scrapy
from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class BeobankBESpider(StructuredDataSpider):
    name = "beobank_be"
    item_attributes = {"brand": "Beobank", "brand_wikidata": "Q14911971"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        headers = {
            "Accept": "text/json; charset=utf-8, text/xml; charset=utf-8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.beobank.be",
            "Referer": "https://www.beobank.be/nl/resultaat-kantoren.html?search=bruges&selectedServicesValues=1&selectedMarketTypeValues=0&selectedOpeningDaysValues=0&selectedPoiTypeValue=2",
            "x-TargetApplicationBlockId": "C",
        }
        for type in ["1", "2"]:
            payload = f"Data_SelectedPoiTypeValue={type}&Bool%3AData_SearchListOpeningDay_CheckBoxListItemViewModel_Checked=false&Bool%3AData_SearchListOpeningDay_CheckBoxListItemViewModel_2__Checked=false&Bool%3AData_SearchListOpeningDay_CheckBoxListItemViewModel_3__Checked=false&%5Bt%3Axsd%253astring%3B%5DData_Search=bruges&%24CPT=MAA%2FYZJNhqGAA6AQKYL1bMAyvuDg3KTxPkrRi7hPak6kqzQ56QLo0Kgjzw6yHtzlXz5N5f7zINBWfU17IC0tSO%2BbvkK5%2Fm9z9B2sPcFrsC6Z%2BUptmVLiHjf7UYYsT8ChHfFfZ8YJ6m6Sa1JiiDD2Za6%2FRQMVdXihLkbC9lrgfhd2vU6Eox2z%2FHL%2BnNr8RgzffndirqdUkHL6Ck92LY4kxCyTfC%2BPxzSImsLJO9HLaTAQkRFA2kEvxyUiDTyYq1fXI2s2oLyxB7c%2FjleQ%2FWGQ3tpowQUb3abALIODzIVsUrHoMwqXxLe%2Fj7QcIV5NJhEIPLfr%2BZfqq2KdzWUEJ79iyYNU3AtBLkMwiEojN0%2F9TOEDctZRspQ5vNmcgPkwX9GytHf3onZ6j4PSpupsR9423%2BhHv4r%2Bwa9EQ1%2BD07GwP2vVjw%3D%3D&_wxf2_cc=nl-BE%2Fnl-NL&_FID_DoLoadMoreResults=&Data_SearchListOpeningDaySelectedItemsCount=0&Data_CurrentPageIndex=31&Data_SelectedMarket=&Data_IsSearchDone=true&%5Bt%3Axsd%253astring%3B%5DData_SearchInseeCode=&Data_SearchListMarketTypesSelectedItemsCount=0&Data_SearchListServicesSelectedItemsCount=0&Data_SelectedServicesValues=0&Data_SelectedMarketTypeValues=0&Data_SelectedOpeningDaysValues=0&_wxf2_pseq=32&_wxf2_pmode=Normal&_wxf2_ptarget=C%3AP%3Aup"
            yield scrapy.Request(
                url="https://www.beobank.be/nl/resultaat-kantoren.html?_tabi=C&_pid=SearchResults&k_search=bruges&k_selectedServicesValues=1&k_selectedMarketTypeValues=0&k_selectedOpeningDaysValues=0&k_selectedPoiTypeValue=2",
                body=payload,
                cb_kwargs={"location_type": type},
                method="POST",
                headers=headers,
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
                yield scrapy.Request(url=link, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.BANK, item)
        yield item
