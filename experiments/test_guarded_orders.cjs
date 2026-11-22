'use strict';

const assert = require('node:assert/strict');
const {makeGuardedStudy, guardedFruit} = require('./guarded_orders.cjs');

const fruit = guardedFruit();
function fruitOutcome([a, p, t], steps) {
  for (const name of steps) {
    if (name === 'S') { t += a; a = 0; }
    if (name === 'D') t *= 2;
    if (name === 'G' && (a + t) % 2 === 1) return null;
  }
  return {total: BigInt(a + p + t)};
}
const orders = [];
for (let a = 0; a < 4; a++) {
  for (let p = 0; p < 4; p++) {
    for (let t = 0; t < 4; t++) orders.push([a, p, t]);
  }
}
assert.equal(fruit.classCount, 4);
let fruitPairs = 0;
for (const x of orders) for (const y of orders) {
  const evenCountDiffers = (x[0] + x[2]) % 2 !== (y[0] + y[2]) % 2;
  const unmarkedDiffers = x[0] % 2 !== y[0] % 2;
  const length = evenCountDiffers ? 1 : unmarkedDiffers ? 2 : null;
  const admission = fruit.admissionWitness(x, y);
  assert.equal(admission?.steps.length ?? null, length);
  assert.equal(fruit.classOf(x) === fruit.classOf(y), length === null);
  if (admission) {
    assert.equal(admission.left, fruitOutcome(x, admission.steps) !== null);
    assert.equal(admission.right, fruitOutcome(y, admission.steps) !== null);
  }
  const found = fruit.distinguish(x, y);
  assert.equal(found === null, x === y); // Each composition occurs once in orders.
  if (found) {
    assert.ok(found.steps.length <= 2);
    assert.deepEqual(found.left, fruitOutcome(x, found.steps));
    assert.deepEqual(found.right, fruitOutcome(y, found.steps));
    assert.notDeepEqual(found.left, found.right);
  }
  fruitPairs++;
}
assert.deepEqual(fruit.admissionWitness([2, 2, 0], [1, 2, 1]), {
  steps: ['D', 'G'], left: true, right: false
});
assert.equal(fruit.admissionWitness([2, 2, 0], [0, 2, 2]), null);
assert.deepEqual(fruit.distinguish([2, 2, 0], [0, 2, 2]), {
  steps: ['D'], left: {total: 4n}, right: {total: 6n}
});

// A separate forward search follows the actual stocks, including failed prefixes.
// These test recipes cannot increase stock, so exhausting the queue covers all words.
function forwardLength(left, right, step, withReading) {
  const queue = [[left, right, 0]];
  const seen = new Set();
  for (let i = 0; i < queue.length; i++) {
    const [u, v, length] = queue[i];
    if ((u === null) !== (v === null)) return length;
    if (u === null) continue;
    if (withReading && u[0] + u[1] !== v[0] + v[1]) return length;
    const key = u.join(',') + '/' + v.join(',');
    if (seen.has(key)) continue;
    seen.add(key);
    for (const op of ['A', 'B']) queue.push([step(u, op), step(v, op), length + 1]);
  }
  return null;
}
const small = [];
for (let a = 0; a <= 2; a++) for (let p = 0; p <= 2; p++) small.push([a, p]);
const A = [[[0, 1], [1, 0]], [[1, 1], [0, 0]]];
const B = [[[0, 0], [0, 1]], [[0, 0], [1, 0]]];
const maskAllows = (mask, digit) => Boolean(mask & (1 << Number(digit)));
let menus = 0, comparisons = 0;
for (const [i, aMatrix] of A.entries()) for (const [j, bMatrix] of B.entries()) {
  for (let aMask = 0; aMask < 4; aMask++) for (let bMask = 0; bMask < 4; bMask++) {
    const study = makeGuardedStudy(2, 2, {A: aMatrix, B: bMatrix}, {
      A: r => maskAllows(aMask, r[0]), B: r => maskAllows(bMask, r[1])
    }, {total: [1, 1]});
    function step(stock, op) {
      if (stock === null) return null;
      const [a, p] = stock;
      if (op === 'A' && maskAllows(aMask, a % 2)) return i === 0 ? [p, a] : [a + p, 0];
      if (op === 'B' && maskAllows(bMask, p % 2)) return j === 0 ? [0, p] : [0, a];
      return null;
    }
    function total(stock, word) {
      const result = word.reduce(step, stock);
      return result === null ? null : {total: BigInt(result[0] + result[1])};
    }
    for (const x of small) for (const y of small) {
      const word = study.distinguish(x, y);
      assert.equal(word?.steps.length ?? null, forwardLength(x, y, step, true));
      if (word) {
        assert.deepEqual(word.left, total(x, word.steps));
        assert.deepEqual(word.right, total(y, word.steps));
        assert.notDeepEqual(word.left, word.right);
      }
      const witness = study.admissionWitness(x, y);
      assert.equal(witness?.steps.length ?? null, forwardLength(x, y, step, false));
      if (witness) {
        assert.equal(witness.left, total(x, witness.steps) !== null);
        assert.equal(witness.right, total(y, witness.steps) !== null);
        assert.notEqual(witness.left, witness.right);
      }
      comparisons++;
    }
    menus++;
  }
}

// Both odd-apple stocks block A. Its hypothetical numerical outputs are unobservable.
const hidden = makeGuardedStudy(2, 2, {A: [[2, 0], [0, 1]]},
  {A: r => r[0] === 0n}, {total: [1, 1]});
assert.equal(hidden.distinguish([1, 3], [3, 1]), null);
const erase = makeGuardedStudy(2, 2, {E: [[0, 0], [0, 0]]},
  {E: r => r[0] === 0n}, {total: [1, 1]});
assert.deepEqual(erase.distinguish([0, 1], [1, 0]), {
  steps: ['E'], left: {total: 0n}, right: null
});
assert.equal(erase.observe([1, 0], ['E', 'E']), null);
const empty = makeGuardedStudy(1, 1, {}, {}, {});
assert.equal(empty.classCount, 1);
assert.deepEqual(empty.observe([9]), {});
assert.equal(empty.distinguish([0], [50]), null);
const mod4 = makeGuardedStudy(1, 4, {D: [[2]], G: [[1]]}, {G: r => r[0] === 0n}, {});
assert.equal(mod4.classCount, 3);
assert.deepEqual(mod4.admissionWitness([2], [1]).steps, ['D', 'G']);
assert.deepEqual(mod4.distinguish([2], [1]), {steps: ['D', 'G'], left: {}, right: null});
const huge = 10n ** 35n;
assert.deepEqual(fruit.observe([huge, 1n, 2n], ['D', 'G']), {total: huge + 5n});
const signed = makeGuardedStudy(2, 1, {}, {}, {balance: [1, -1]});
assert.deepEqual(signed.observe([0n, huge]), {balance: -huge});
assert.throws(() => makeGuardedStudy(1, 0, {}, {}, {}), RangeError);
assert.throws(() => makeGuardedStudy(1, 2, {}, {typo: () => true}, {}), RangeError);
assert.throws(() => makeGuardedStudy(1, 2, {G: [[1]]}, {G: () => 1}, {}), TypeError);
assert.throws(() => fruit.observe([0, -1, 0]), RangeError);
assert.throws(() => fruit.observe([0, 1, 0], ['?']), RangeError);

// Withdrawing one pair at a time reveals an unbounded number through admission alone.
function tryPairs(n, steps) {
  for (const step of steps) {
    if (step === 'G' && n % 2) return false;
    if (step === 'B') {
      if (n < 2) return false;
      n -= 2;
    }
  }
  return true;
}
for (let n = 0; n < 128; n++) {
  const withdrawals = [];
  while (tryPairs(n, [...withdrawals, 'B'])) withdrawals.push('B');
  assert.equal(2 * withdrawals.length + Number(!tryPairs(n, ['G'])), n);
}
let words = [[]];
for (let limit = 0; limit <= 8; limit++) {
  for (const w of words) assert.equal(tryPairs(2 * limit, w), tryPairs(2 * limit + 2, w));
  const witness = Array(limit + 1).fill('B');
  assert.equal(tryPairs(2 * limit, witness), false);
  assert.equal(tryPairs(2 * limit + 2, witness), true);
  words = [[], ...words.flatMap(w => [[...w, 'G'], [...w, 'B']])];
}
const triples = makeGuardedStudy(1, 3, {G: [[1]]}, {G: r => r[0] === 0n}, {});
assert.equal(triples.classOf([1]), triples.classOf([2]));
assert.notEqual(triples.classOf([1 + 1]), triples.classOf([2 + 1]));

console.log('PASS: four admission classes, ' + fruitPairs + ' ordered fruit-stock pairs');
console.log('PASS: complete forward search for ' + menus + ' menus, ' + comparisons + ' pairs');
console.log('PASS: guarded zero, masked outputs, composite modulus, exact arithmetic, removal and addition');
