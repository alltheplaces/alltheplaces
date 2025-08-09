from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import FIREFOX_LATEST


class MatsukiyoJPSpider(Spider):
    name = "matsukiyo_jp"
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept-Encoding": "gzip, deflate, br, zstd", 
            "Accept-Language": "ja",
            "Connection": "keep-alive",
            "Referer": "https://www.matsukiyococokara-online.com/map/search",
            "user-agent": FIREFOX_LATEST,  # needed for success
        }
    }
    start_urls = ["https://www.matsukiyococokara-online.com/map/s3/json/stores.json"]
    allowed_domains = ["www.matsukiyococokara-online.com"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            match store["icon"]:
                case 1:
                    item.update({"brand": "マツモトキヨシ", "brand_wikidata": "Q8014776"})
                case 3:
                    item.update({"brand": "matsukiyoLAB", "brand_wikidata": "Q8014776"})
                case 4:
                    item.update({"brand": "ファミリードラッグ"})
                case 9:
                    item.update({"brand": "petit madoca"})
                case 12:
                    item.update({"brand": "くすりのラブ", "brand_wikidata": "Q11347308"})
                case 14:
                    item.update({"brand": "シメノドラッグ", "brand_wikidata": "Q11588146"})
                case 15:
                    item.update({"brand": "ダルマ", "brand_wikidata": "Q11317431"})
                case 16:
                    item.update({"brand": "ぱぱす", "brand_wikidata": "Q11276061"})
                case 17:
                    item.update({"brand": "ヘルスバンク", "brand_wikidata": "Q11522264"})
                case 18:
                    item.update({"brand": "ミドリ薬品"})
                case 19:
                    item.update({"brand": "ココカラファイン", "brand_wikidata": "Q11301948"})
                case 30:
                    item.update({"brand": "ココカラファイン", "brand_wikidata": "Q11301948"})
                case 31:
                    item.update({"brand": "セイジョー", "brand_wikidata": "Q11314133"})
                case 32:
                    item.update({"brand": "ドラッグセガミ", "brand_wikidata": "Q11301949"})
                case 33:
                    item.update({"brand": "ジップドラッグ", "brand_wikidata": "Q11309539"})
                case 34:
                    item.update({"brand": "ライフォート", "brand_wikidata": "Q11346469"})
                case 35:
                    item.update({"brand": "クスリのコダマ", "brand_wikidata": "Q11302198"})
                case 36:
                    item.update({"brand": "ココカラファインイズミヤ"})
                case 37:
                    item.update({"brand": "クスリ岩崎チェーン"})

            if store["businesshours"][2] == "1":
                item["opening_hours"] = "24/7"

            apply_category(Categories.SHOP_CHEMIST, item)
            yield item
