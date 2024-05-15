from typing import Iterable
from urllib.parse import urljoin

import jsonpath_ng as jsonpath
from scrapy.http import JsonRequest, TextResponse

from store_scrap.items import Product
from store_scrap.spiders.storescrap import StoreScrapSpider


class ExtraSpider(StoreScrapSpider):
    name = "extra"
    allowed_domains = ["ml6pm6jwsi-3.algolianet.com"]

    per_page = 48

    def get_payload(self, category, page=0):
        return {"requests":[
            # {"indexName": "prod_sa_product_index", "query":"",
            #  "params":f"optionalFilters=%5B%22sellingOutFastCities%3ASA-tabuk%3Cscore%3D5%3E%22%2C%22inStockCities%3ASA-tabuk%3Cscore%3D5%3E%22%5D&facets=%5B%22productFeaturesAr.*%22%2C%22brandAr%22%2C%22subFamilyAr%22%2C%22rating%22%2C%22productStatusAr%22%2C%22price%22%2C%22offersFacet%22%2C%22inStock%22%2C%22hasFreeGifts%22%2C%22familyAr%22%2C%22deliveryFacet%22%5D&hitsPerPage=1&page=0&getRankingInfo=1&clickAnalytics=false&filters=categories%3A{category}&facetFilters=%5B%5B%22sponsoredType%3AEXTRASPECIAL%22%5D%5D"},
            # {"indexName":"prod_sa_product_index","query":"",
            #  "params":f"optionalFilters=%5B%22sellingOutFastCities%3ASA-tabuk%3Cscore%3D5%3E%22%2C%22inStockCities%3ASA-tabuk%3Cscore%3D5%3E%22%5D&facets=%5B%22productFeaturesAr.*%22%2C%22brandAr%22%2C%22subFamilyAr%22%2C%22rating%22%2C%22productStatusAr%22%2C%22price%22%2C%22offersFacet%22%2C%22inStock%22%2C%22hasFreeGifts%22%2C%22familyAr%22%2C%22deliveryFacet%22%5D&hitsPerPage=2&page=0&getRankingInfo=1&clickAnalytics=false&filters=categories%3A{category}&facetFilters=%5B%5B%22sponsoredType%3ASPONSORED%22%5D%5D"},
            {"indexName": "prod_sa_product_index", "query": "",
             "params":f"optionalFilters=%5B%22sellingOutFastCities%3ASA-tabuk%3Cscore%3D5%3E%22%2C%22inStockCities%3ASA-tabuk%3Cscore%3D5%3E%22%5D&facets=%5B%22productFeaturesAr.*%22%2C%22brandAr%22%2C%22subFamilyAr%22%2C%22rating%22%2C%22productStatusAr%22%2C%22price%22%2C%22offersFacet%22%2C%22inStock%22%2C%22hasFreeGifts%22%2C%22familyAr%22%2C%22deliveryFacet%22%5D&hitsPerPage={self.per_page}&page={page}&getRankingInfo=1&clickAnalytics=true&filters=categories%3A{category}&facetFilters=%5B%5D"}
        ]}

    brand_values = {
        'Admiral': 'ADMIRL',
        'Hisense': 'HISENSE',
        'Samsung': 'SAMSNG',
    }

    products_pattern = jsonpath.parse('$.results[*].hits[*]')

    api_url = 'https://ml6pm6jwsi-3.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.5.1)%3B%20Browser%20(lite)&x-algolia-api-key=af1b13cfdc69ebf18c5980f2c6afff4d&x-algolia-application-id=ML6PM6JWSI'

    def start_requests(self) -> Iterable[JsonRequest]:
        for brand in self.brands:
            if brand in self.brand_values:
                request = JsonRequest(
                    url=self.api_url,
                    headers=self.headers,
                    data=self.get_payload(self.brand_values[brand], page=0),
                    callback=self.parse,
                    cb_kwargs={'page': 0, 'category': self.brand_values[brand]}
                )
                yield request

    def parse(self, response: TextResponse, category: str, page: int) -> Iterable[Product | JsonRequest]:
        json_data = response.json()
        products = list(map(lambda m: m.value, self.products_pattern.find(json_data)))
        for product in products:
            yield Product(
                name_ar=product['nameAr'],
                name_en=product['nameEn'],
                description_ar=product['descriptionAr'],
                description_en=product['descriptionEn'],
                price_original=product['wasPrice'],
                price_discounted=product['price'],
                brand_ar=product['brandAr'],
                brand_en=product['brandEn'],
                link=urljoin('https://www.extra.com/', product.get('urlAr', product['urlEn'])),
                sku=self.get_model_code(product['descriptionEn']),
                id=product['barCode'][0] if product.get('barCode') else ''
            )
        if len(products) == self.per_page:
            yield JsonRequest(
                url=self.api_url,
                headers=self.headers,
                data=self.get_payload(category, page=page + 1),
                callback=self.parse,
                cb_kwargs={'page': page + 1, 'category': category}
            )

    def get_model_code(self, product_name: str):
        parts = product_name.split('--', 1)
        if len(parts) == 1:
            parts = product_name.split('-', 1)
        return parts[0].strip()

    @property
    def origin(self):
        return "https://www.extra.com/"
