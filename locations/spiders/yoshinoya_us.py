from locations.storefinders.where2getit import Where2GetItSpider


class YoshinoyaUSSpider(Where2GetItSpider):
    name = "yoshinoya_us"
    item_attributes = {"brand": "Yoshinoya", "brand_wikidata": "Q776272"}
    api_brand_name = "yoshinoyasites"
    api_key = "5F63337C-CAA5-11EE-A3D6-FED4D2F445A6"
