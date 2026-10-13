from typing import AsyncIterator, Iterable

from chompjs import chompjs
from scrapy import Request
from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature, SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiBRSpider(JSONBlobSpider):
    name = "mitsubishi_br"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.mitsubishimotors.com.br/concessionarias",
            method="POST",
            body="[]",
            # The Next.js Server Action ID looks persistent.
            headers={"next-action": "00a80ca9fb048328a749f272aee51ddac87f340448"},
        )

    def extract_json(self, response: TextResponse) -> list[dict]:
        return list(chompjs.parse_js_objects(response.text))[-1]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("geodata", {}))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["id_integracao"]
        item["state"] = feature.get("estado")
        if not item.get("addr_full"):
            item["addr_full"] = feature.get("endereco")
        item["phone"] = "; ".join(filter(None, [feature.get("telefone"), feature.get("telefone2")]))
        set_social_media(item, SocialMedia.WHATSAPP, (feature.get("whatsapp") or ""))

        services = feature.get("servicos") or {}
        if services.get("novos"):
            sales_item = item.deepcopy()
            sales_item["ref"] = f"{item['ref']}-sales"
            apply_category(Categories.SHOP_CAR, sales_item)
            apply_yes_no(Extras.VEHICLE_USED_CAR_SALES, sales_item, services.get("seminovos"))
            yield sales_item

        if services.get("revisao_programada") or services.get("funilaria"):
            service_item = item.deepcopy()
            service_item["ref"] = f"{item['ref']}-service"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item

        if services.get("kit_pecas"):
            parts_item = item.deepcopy()
            parts_item["ref"] = f"{item['ref']}-parts"
            apply_category(Categories.SHOP_CAR_PARTS, parts_item)
            yield parts_item

        if not services:
            apply_category(Categories.SHOP_CAR, item)
            yield item
