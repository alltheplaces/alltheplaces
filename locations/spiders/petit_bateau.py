import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PetitBateauSpider(SitemapSpider, StructuredDataSpider):
    name = "petit_bateau"
    item_attributes = {"brand": "Petit Bateau", "brand_wikidata": "Q3377090"}
    sitemap_urls = ["https://stores.petit-bateau.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/stores\.petit-bateau\.com\/[a-z\-]{3,}\/.+", "parse_sd")]
    wanted_types = ["ClothingStore"]
    drop_attributes = {"image"}

    LOCATED_IN = [
        (["Galeries Lafayette"], ("Galeries Lafayette", "Q3094686")),
        (["Nouvelles Galeries"], ("Nouvelles Galeries", "Q3345246")),
        (["Manor"], ("Manor", "Q382686")),
        (["Globus"], ("Globus", "Q683505")),
        (["髙島屋", "高島屋", "Takashimaya"], ("髙島屋", "Q2058024")),
        (["伊勢丹", "Isetan"], ("伊勢丹", "Q3155239")),
        (["東武百貨店", "Tobu"], ("東武百貨店", "Q11235004")),
        (["藤崎", "Fujisaki"], ("藤崎", "Q11288204")),
        (["大丸", "Daimaru"], ("大丸", "Q3012112")),
        (["阪急", "Hankyu"], ("阪急百貨店", "Q5648576")),
        (["近鉄", "Kintetsu"], ("近鉄百貨店", "Q6414357")),
        (["三越", "Mitsukoshi"], ("三越", "Q1065598")),
        (["鶴屋", "Tsuruya"], ("鶴屋百貨店", "Q11675938")),
        (["岩田屋", "Iwataya"], ("岩田屋", "Q6100771")),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        name = item.pop("name")
        for keywords, (located_in, located_in_wikidata) in self.LOCATED_IN:
            if any(keyword.lower() in name.lower() for keyword in keywords):
                item["located_in"] = located_in
                item["located_in_wikidata"] = located_in_wikidata
                break
        else:
            if not re.search(r"(?i)petit\s*bateau|プチバトー", name):
                # Multi-brand stockist, not a Petit Bateau shop
                return

        item["branch"] = (
            re.sub(r"(?i)rivenditore\s+monomarca|petit\s*bateau|プチバトー(?:POPUP)?(?:ショップ)?", "", name).strip(
                " -:　"
            )
            or None
        )
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
