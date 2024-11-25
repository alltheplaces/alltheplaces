from locations.spiders.nevada_dot_us import NevadaDotUSSpider


# TODO: all cameras in NY apart from some in CT
class NewYorkDotUSSpider(NevadaDotUSSpider):
    name = "new_york_dot_us"
    item_attributes = {"operator": "New York State DOT", "operator_wikidata": "Q527769"}
    start_urls = ["https://511ny.org/map/mapIcons/Cameras"]
