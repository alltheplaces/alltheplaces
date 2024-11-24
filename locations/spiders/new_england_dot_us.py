from typing import Any

from locations.items import Feature
from locations.pipelines.state_clean_up import StateCodeCleanUpPipeline
from locations.spiders.nevada_dot_us import NevadaDotUSSpider


class NewEnglandDotUSSpider(NevadaDotUSSpider):
    name = "new_england_dot_us"
    item_attributes = {}
    NEW_ENGLAND_DOTS = {
        "ME": {"operator": "Maine DOT", "operator_wikidata": "Q4926312"},
        "NH": {"operator": "New Hampshire DOT", "operator_wikidata": "Q5559073"},
        "VT": {"operator": "Vermont Agency of Transportation", "operator_wikidata": "Q7921675"},
    }
    start_urls = ["https://www.newengland511.org/map/mapIcons/Cameras"]
    # List of pipelines that we want to have callbacks from.
    pipeline_after_callbacks = [StateCodeCleanUpPipeline]

    # All callbacks come through the same method with the pipeline calling being
    # passed as an argument in the unlikely case that the spider wants callbacks
    # from multiple pipelines and so a dispatch could be done in the spider callback,
    def pipeline_after_callback(self, item: Feature, pipeline: Any) -> Feature | None:
        if not item["state"]:
            # A couple of cameras do not reverse geocode.
            item["state"] = "VT"
        item.update(self.NEW_ENGLAND_DOTS.get(item["state"], {}))
        return item
