from locations.spiders.nevada_dot_us import NevadaDotUSSpider


class FloridaDotUSSpider(NevadaDotUSSpider):
    name = "florida_dot_us"
    item_attributes = {"operator": "Florida DOT", "operator_wikidata": "Q3074270"}
    start_urls = ["https://www.fl511.com/map/mapIcons/Cameras"]
