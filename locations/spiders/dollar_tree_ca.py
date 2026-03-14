from locations.spiders.dollar_tree_us import DollarTreeUSSpider


class DollarTreeCASpider(DollarTreeUSSpider):
    name = "dollar_tree_ca"
    experience_key = "pages-locator-canada-only"
    feature_type = "dollar-tree-canada"
