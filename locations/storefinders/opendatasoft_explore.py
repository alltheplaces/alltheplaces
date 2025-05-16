from datetime import UTC, datetime, timedelta
from typing import Iterable
from urllib.parse import quote_plus, urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.items import Feature


class OpendatasoftExploreSpider(Spider):
    """
    The Opendatasoft Explore API is used for providing open data portals,
    primarily for government organisations. The API is documented at:
    https://help.opendatasoft.com/apis/ods-explore-v2/explore_v2.1.html

    To use this class, specify `api_endpoint` as the URL including the path up
    to `/api/explore/v2.1/` for the Opendatasoft Explore API instance to
    query. Also specify the `dataset_id` attribute as the name of the dataset
    to extract features from. Optionally specify `field_names` if it is
    beneficial to only work with a subset of all fields available within the
    layer.

    Each feature within the specified layer is run through `DictParser.parse`
    to try and automatically extract as much information as possible. Override
    the `pre_process_data` function to modify field values before
    `DictParser.parse` is called. Override the `post_process_item` function to
    extract additional information from the source feature or to clean data
    after automatic extraction has been attempted.

    Warnings will be raised if any of the following conditions occur:
      1. Source data has a last data modification timestamp greater than 365
         days ago. This warning is a prompt to double check the latest source
         data is in use and that the brand/operator hasn't changed systems for
         publishing geographic information about features.
      2. A field defined in the `field_names` attribute is not present in the
         requested dataset. This may indicate the data publisher has changed
         the schema of the dataset to omit, rename or replace a field.
    """

    dataset_attributes = {"source": "api", "api": "opendatasoft"}

    api_endpoint: str = ""
    dataset_id: str = ""
    field_names: list[str] = []

    # ATP is not a robot in the way that robots.txt intends.
    # Datasets are often quite large and may take a while to export and
    # download. The download size warning is increased to 256MiB.
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 120, "DOWNLOAD_WARNSIZE": 268435456}

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url=urljoin(self.api_endpoint, f"catalog/datasets/{self.dataset_id}"), callback=self.parse_dataset_metadata
        )

    def parse_dataset_metadata(self, response: Response) -> Iterable[JsonRequest]:
        metadata = response.json()["metas"]["default"]
        timestamp_of_last_edit = datetime.fromisoformat(metadata["data_processed"])
        self.dataset_attributes.update({"source:date": timestamp_of_last_edit.isoformat()})
        current_timestamp = datetime.now(UTC)
        if current_timestamp - timestamp_of_last_edit > timedelta(days=365):
            self.logger.warning(
                "The requested dataset is possibly outdated as it was last edited over 365 days ago on {}.".format(
                    timestamp_of_last_edit.isoformat()
                )
            )

        url_parameters = ""
        if len(self.field_names) > 0:
            available_field_names = [field["name"] for field in response.json()["fields"]]
            output_field_names = []
            for field_name in self.field_names:
                if field_name not in available_field_names:
                    self.logger.warning(
                        "Spider requested that field `{}` be extracted for each feature in the dataset but the dataset doesn't have a field named `{}`. Field ignored.".format(
                            field_name, field_name
                        )
                    )
                    continue
                output_field_names.append(field_name)
            output_fields = ",".join(map(quote_plus, output_field_names))
            url_parameters = f"?select={output_fields}"

        self.logger.info(
            "Exporting and downloading requested dataset `{}`. This may take a few minutes to complete.".format(
                self.dataset_id
            )
        )
        yield JsonRequest(
            url=urljoin(self.api_endpoint, f"catalog/datasets/{self.dataset_id}/exports/geojson{url_parameters}"),
            callback=self.parse_dataset_records,
        )

    def parse_dataset_records(self, response: Response) -> Iterable[Feature]:
        features = response.json()["features"]

        for feature in features:
            properties = feature.pop("properties")
            if "geometry" in properties.keys():
                # Prevent unlikely (but still possible) overwriting of feature
                # geometry if GeoJSON properties include a "geometry" field.
                properties["__geometry"] = properties.pop("geometry")
            feature.update(properties)
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            yield from self.post_process_item(item, response, feature)

    def pre_process_data(self, feature: dict) -> None:
        return

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        yield item
