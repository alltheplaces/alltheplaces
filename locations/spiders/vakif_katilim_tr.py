import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class VakifKatilimTRSpider(scrapy.Spider):
    name = "vakif_katilim_tr"
    item_attributes = {"brand": "Vakıf Katılım", "brand_wikidata": "Q31188912"}
    start_urls = ["https://www.vakifkatilim.com.tr/tr/diger/subeler-ve-atmler"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        lang_id = response.xpath('//script[contains(text(), "langId:")]//text()').re_first(r"langId:\s*'([^']+)'")

        pois_url = f"https://www.vakifkatilim.com.tr/plugins/Informations?langId={lang_id}&slug=sube-ve-atm"
        yield scrapy.Request(pois_url, callback=self.parse_pois)

    def parse_pois(self, response):
        data = response.json()
        for poi in data.get("information"):
            item = DictParser.parse(poi)
            item["ref"] = poi.get("branchType")
            item["extras"]["addr:district"] = poi.get("districtName")
            if poi.get("type"):
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)
            # TODO: capture "isHandicapped" and "isBlind" attributes
            yield item
