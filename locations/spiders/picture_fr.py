from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature, SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider


class PictureFRSpider(JSONBlobSpider):
    name = "picture_fr"
    item_attributes = {"brand": "Picture", "brand_wikidata": "Q132088335"}
    start_urls = ["https://www.picture-organic-clothing.com/fr-fr/pages/store-locator?view=stores-data"]
    locations_key = "features"
    name_is_branch = True

    def parse(self, response: TextResponse) -> Iterable:
        yield from super().parse(response)
        data = response.json()
        if data["page"] < data["pages"]:
            yield response.follow(f"{self.start_urls[0]}&{data['page_param']}={data['page'] + 1}")

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # The locator also lists stockists; only own stores are flagged
        if not feature["picture_store"]:
            return
        item["branch"] = item["branch"].removeprefix("PICTURE STORE ")
        set_social_media(item, SocialMedia.INSTAGRAM, item.pop("website"))
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
