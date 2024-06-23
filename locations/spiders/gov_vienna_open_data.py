from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.items import Feature


class GovOpenDataViennaSpider(Spider):
    # dataset_id: str = None
    dataset_id: str = None

    # The format in which to download the dataset.
    # Usually listed in result.resources[].format in dataset metadata, example:
    # https://www.data.gv.at/katalog/api/3/action/package_show?id=1354c278-387b-4b52-9b68-9cf270761a66
    dataset_download_format: str = "JSON"

    api_url = "https://www.data.gv.at/katalog/api/3/"

    def start_requests(self) -> Iterable[Request]:
        url_template = self.api_url + "action/package_show?id={}"
        yield Request(url_template.format(self.dataset_id))

    def parse(self, response: Response):
        dataset = response.json()["result"]
        for resource in dataset["resources"]:
            if resource["format"] == self.dataset_download_format:
                if resource["state"] != "active":
                    raise ValueError(f"Resource {resource['id']} at {response.url} is not active.")
                yield Request(resource["url"], callback=self.parse_file, meta={"dataset_metadata": dataset})

    def parse_file(self, response: Response) -> Iterable[Feature]:
        raise NotImplementedError("Subclasses must implement this method.")


class GovOpenDataViennaTourismSpider(GovOpenDataViennaSpider):
    name = "gov_open_data_vienna_tourist_attractions"
    dataset_id = "1354c278-387b-4b52-9b68-9cf270761a66"
    dataset_download_format = "JSON"

    def parse_file(self, response: Response) -> Iterable[Feature]:
        data = response.json()
        for item in data:
            yield item
