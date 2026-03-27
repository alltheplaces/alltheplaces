import gzip
import json
from pathlib import Path
from typing import Any, AsyncIterator

import boto3
from scrapy.http import JsonRequest, Response

from locations.address_spider import AddressSpider
from locations.items import Feature


class OpenAddressesSpider(AddressSpider):
    source: str

    async def start(self) -> AsyncIterator[Any]:
        assert self.source
        yield JsonRequest("https://batch.openaddresses.io/api/data")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for dataset in response.json():
            if dataset["layer"] != "addresses":
                continue
            if dataset["source"] != self.source:
                continue
            yield JsonRequest(
                "https://batch.openaddresses.io/api/job/{}".format(dataset["job"]),
                callback=self.parse_job,
                cb_kwargs={"dataset": dataset},
            )
            break
        else:
            raise Exception("Dataset not found")

    def parse_job(self, response: Response, dataset: dict, **kwargs: Any) -> Any:
        local_file = Path(self.settings.get("FILES_STORE", "/tmp/atp")) / self.name
        local_file.parent.mkdir(exist_ok=True, parents=True)
        if not local_file.exists():  # TODO: no AWS key
            client = boto3.client("s3")
            client.download_file(
                "v2.openaddresses.io", response.json()["s3"].removeprefix("s3://v2.openaddresses.io/"), local_file
            )
        with gzip.open(local_file) as f:
            country = self.source.split("/", 1)[0].upper()
            for line in f:
                item = self.parse_feature(json.loads(line))
                item["country"] = country
                yield item

    def parse_feature(self, feature: dict) -> Feature:
        item = Feature()
        item["geometry"] = feature["geometry"]

        # OA outputs nulls as empty strings, adding "or None" here means our output is None and item_attributes or other pipelines apply
        item["ref"] = feature["properties"]["hash"]  #  feature["properties"]["id"]?
        item["housenumber"] = feature["properties"]["number"] or None
        item["street"] = feature["properties"]["street"] or None
        item["extras"]["addr:unit"] = feature["properties"]["unit"] or None
        item["city"] = feature["properties"]["city"] or None
        item["extras"]["addr:district"] = feature["properties"]["district"] or None  # ?
        item["extras"]["addr:region"] = feature["properties"]["region"] or None  # ?
        item["postcode"] = feature["properties"]["postcode"] or None
        item["extras"]["accuracy"] = feature["properties"]["accuracy"] or None  # ?

        return item
