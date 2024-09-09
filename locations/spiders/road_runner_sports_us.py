from locations.storefinders.rio_seo import RioSeoSpider


class RoadRunnerSportsUSSpider(RioSeoSpider):
    name = "road_runner_sports_us"
    item_attributes = {
        "brand_wikidata": "Q113494713",
        "brand": "Road Runner Sports",
    }
    end_point = "https://maps.stores.roadrunnersports.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
