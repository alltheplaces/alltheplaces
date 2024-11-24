from locations.spiders.nevada_dot_us import NevadaDotUSSpider


class GeorgiaDotUSSpider(NevadaDotUSSpider):
    name = "georgia_dot_us"
    item_attributes = {"operator": "Georgia DOT", "operator_wikidata": "Q944993"}
    start_urls = ["https://511ga.org/map/mapIcons/Cameras"]
