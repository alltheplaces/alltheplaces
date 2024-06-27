from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.exporters.geojson import mapping
from locations.items import Feature


class AllThePlacesSpider(Spider):
    """
    This class can help parse ATP style geojson files (from https://www.alltheplaces.xyz/spiders.html, or other sources)
    to allow for the data to be processed through different exporters or pipelines.
    """

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for feature in response.json().get("features", []):
            properties = feature.get("properties", {})

            item = Feature()

            for atp_key, json_key in mapping:
                if value := properties.pop(json_key, None):
                    item[atp_key] = value

            item["ref"] = properties.pop("ref", None)
            item["geometry"] = feature.get("geometry", {})
            item["extras"] = properties

            yield from self.post_process_feature(item, feature, response) or []

    def post_process_feature(
        self, item: Feature, source_feature: dict, response: Response, **kwargs
    ) -> Iterable[Feature]:
        yield item
