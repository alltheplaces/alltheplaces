from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FivehundredelevenAlbertaCASpider(JSONBlobSpider):
    name = "511_alberta_ca"
    item_attributes = {
        "operator": "Alberta Ministry of Transportation",
        "operator_wikidata": "Q15058324",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["511.alberta.ca"]
    start_urls = ["https://511.alberta.ca/map/mapIcons/Cameras"]
    locations_key = "item2"

    def pre_process_data(self, feature: dict) -> None:
        feature["lat"] = feature["location"][0]
        feature["lon"] = feature["location"][1]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        item["extras"]["camera:type"] = "fixed"
        yield Request(
            url="https://511.alberta.ca/tooltip/Cameras/{}?lang=en-US".format(item["ref"]),
            callback=self.parse_cameras,
            meta={"item": item},
        )

    def parse_cameras(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        for camera_link in response.xpath('//img[contains(@class, "carouselCctvImage")]'):
            camera = item.deepcopy()
            camera["ref"] = camera_link.xpath("./@data-lazy").get().removeprefix("/map/Cctv/")
            camera["name"] = camera_link.xpath("./@title").get()
            camera["extras"]["contact:webcam"] = "https://511.alberta.ca" + camera_link.xpath("./@data-lazy").get()
            camera["extras"]["camera:type"] = "fixed"
            yield camera
