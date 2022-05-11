from locations.brands import Brand


def test_item_from_brand():
    brand = Brand.from_wikidata('Pandora', 'Q2241604')
    item = brand.item('http://www.mysite.com')
    assert 'Pandora' == item['brand']
    assert 'Q2241604' == item['brand_wikidata']
    assert 'http://www.mysite.com' == item['website']
    assert 'http://www.mysite.com' == item['ref']


if __name__ == "__main__":
    test_item_from_brand()
    print("Everything passed")
