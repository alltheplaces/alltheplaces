from locations.extensions.add_lineage import Lineage, spider_class_to_lineage
from locations.spiders.asda_gb import AsdaGBSpider
from locations.spiders.greggs_gb import GreggsGBSpider


def test_class_override():
    AsdaGBSpider.lineage = Lineage.Brands
    assert spider_class_to_lineage(AsdaGBSpider) == Lineage.Brands

    AsdaGBSpider.lineage = Lineage.Aggregators
    assert spider_class_to_lineage(AsdaGBSpider) == Lineage.Aggregators


def test_expected():
    assert spider_class_to_lineage(GreggsGBSpider) == Lineage.Brands
