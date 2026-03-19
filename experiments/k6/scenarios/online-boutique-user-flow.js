import http from 'k6/http';
import { randomItem } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';

export const options = {
  vus: Number(__ENV.VUS || 3000),
  duration: __ENV.DURATION || '4m',
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const OUTPUT = __ENV.OUTPUT || 'k6-summary.json';

const products = [
  '0PUK6V6EV0', '1YMWWN1N4O', '2ZYFJ3GM2N', '66VCHSJNUP', '6E92ZMYYFZ',
  '9SIQT8TOJO', 'L9ECAV7KIM', 'LS4PSXUNUM', 'OLJCESPC7Z'
];

const currencies = ['EUR', 'USD', 'JPY', 'CAD'];

function index() {
  http.get(`${BASE_URL}/`);
}

function setCurrency() {
  http.post(`${BASE_URL}/setCurrency`, { currency_code: randomItem(currencies) });
}

function browseProduct() {
  http.get(`${BASE_URL}/product/${randomItem(products)}`);
}

function viewCart() {
  http.get(`${BASE_URL}/cart`);
}

function addToCart() {
  const product = randomItem(products);
  http.get(`${BASE_URL}/product/${product}`);
  http.post(`${BASE_URL}/cart`, {
    product_id: product,
    quantity: randomItem([1, 2, 3, 4, 5, 10]),
  });
}

function checkout() {
  addToCart();
  http.post(`${BASE_URL}/cart/checkout`, {
    email: 'someone@example.com',
    street_address: '1600 Amphitheatre Parkway',
    zip_code: '94043',
    city: 'Mountain View',
    state: 'CA',
    country: 'United States',
    credit_card_number: '4432-8015-6152-0454',
    credit_card_expiration_month: '1',
    credit_card_expiration_year: '2039',
    credit_card_cvv: '672',
  });
}

const actions = [
  { weight: 1, func: index },
  { weight: 2, func: setCurrency },
  { weight: 10, func: browseProduct },
  { weight: 3, func: viewCart },
  { weight: 2, func: addToCart },
  { weight: 1, func: checkout },
];

export default function () {
  const totalWeight = actions.reduce((sum, a) => sum + a.weight, 0);
  let r = Math.random() * totalWeight;
  for (const action of actions) {
    if (r < action.weight) {
      action.func();
      break;
    }
    r -= action.weight;
  }
}

export function handleSummary(data) {
  return {
    [OUTPUT]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}