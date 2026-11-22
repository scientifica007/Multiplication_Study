'use strict';

const {fruitStudy, makeStudy} = require('./identity_lift.cjs');

function check(ok, label) {
  if (!ok) throw new Error(label);
}
function same(actual, expected, label) {
  const encode = value => JSON.stringify(value, (_, x) =>
    typeof x === 'bigint' ? x.toString() + 'n' : x
  );
  if (encode(actual) !== encode(expected)) {
    throw new Error(label + ': ' + encode(actual) + ' / ' + encode(expected));
  }
}
function rejects(fn, type) {
  try { fn(); } catch (error) {
    if (error instanceof type) return;
    throw error;
  }
  throw new Error('Expected ' + type.name);
}

const fruit = fruitStudy();
const x = [3, 1, 0], y = [1, 3, 0];
for (const steps of [[], ['S'], ['D'], ['D', 'S']]) {
  same([x, y].map(stock => fruit.read(stock, 'total', steps)), [4n, 4n], 'equal totals');
}
same(fruit.distinguish(x, y), {
  reading: 'total', steps: ['S', 'D'], leftValue: 7n, rightValue: 5n
}, 'distinguishing experiment');
same(fruit.run([1, 0, 0], ['S']), fruit.run([0, 0, 1], ['S']), 'marking erases a distinction');
same(fruit.groups(), [[0], [1], [2]], 'three observable types');

let reconstructions = 0;
for (let a = 0n; a <= 3n; a++) {
  for (let p = 0n; p <= 3n; p++) {
    for (let t = 0n; t <= 3n; t++) {
      const stock = [a, p, t];
      const v = fruit.read(stock, 'total');
      const d = fruit.read(stock, 'total', ['D']);
      const sd = fruit.read(stock, 'total', ['S', 'D']);
      same([sd - d, 2n * v - sd, d - v], stock, 'recover the three counts');
      reconstructions++;
    }
  }
}

// A second, forward model handles each original item separately.
// Source j emits matrix[i][j] items of type i under an instruction.
function actOnItems(items, matrix) {
  const result = [];
  for (const j of items) {
    for (let i = 0; i < matrix.length; i++) {
      for (let n = 0; n < matrix[i][j]; n++) result.push(i);
    }
  }
  return result;
}
function allWords(alphabet, depth) {
  let layer = [[]];
  const words = [...layer];
  for (let i = 0; i < depth; i++) {
    layer = layer.flatMap(word => alphabet.map(name => [...word, name]));
    words.push(...layer);
  }
  return words;
}
const matrices = Array.from({length: 16}, (_, bits) => [
  [bits & 1, (bits >> 1) & 1], [(bits >> 2) & 1, (bits >> 3) & 1]
]);
const items = [[], [0], [1], [0, 1]];
const stocks = [[0, 0], [1, 0], [0, 1], [1, 1]];
const words = allWords(['A', 'B'], 3);
let menus = 0, comparisons = 0;
for (const A of matrices) {
  for (const B of matrices) {
    const actions = {A, B};
    const study = makeStudy(2, actions, {total: [1, 1]});
    const forward = items.map(initial => words.map(word =>
      word.reduce((current, step) => actOnItems(current, actions[step]), initial).length
    ));
    for (let i = 0; i < items.length; i++) {
      for (let j = 0; j < items.length; j++) {
        const first = forward[i].findIndex((n, k) => n !== forward[j][k]);
        const found = study.distinguish(stocks[i], stocks[j]);
        if (first < 0) {
          same(found, null, 'indistinguishable');
        } else {
          check(found !== null, 'expected a distinguishing word');
          same(found.steps.length, words[first].length, 'shortest length');
          const k = words.findIndex(word => word.join() === found.steps.join());
          same([found.leftValue, found.rightValue], [BigInt(forward[i][k]), BigInt(forward[j][k])],
            'forward evaluation of the actual witness');
        }
        comparisons++;
      }
    }
    const sameUnits = forward[1].every((n, k) => n === forward[2][k]);
    same(study.groups(), sameUnits ? [[0, 1]] : [[0], [1]], 'grouping agrees with item counts');
    menus++;
  }
}

// Last-stage reading can require d - 1 successive instructions.
for (let d = 1; d <= 6; d++) {
  const move = Array.from({length: d}, (_, i) =>
    Array.from({length: d}, (_, j) => Number(i === j + 1))
  );
  const last = Array.from({length: d}, (_, i) => Number(i === d - 1));
  const first = Array.from({length: d}, (_, i) => Number(i === 0));
  const study = makeStudy(d, {step: move}, {last});
  const witness = study.distinguish(first, Array(d).fill(0));
  same(witness.steps, Array(d - 1).fill('step'), 'sharp length bound');
  same(witness.leftValue, 1n, 'last-stage population');
  same(study.probes.length, d, 'full rank for shift');
}

// Two apple colours can be merged even though pears are distinguished.
const doubleApples = [[2, 0, 0], [0, 2, 0], [0, 0, 1]];
const colours = makeStudy(3, {doubleApples}, {total: [1, 1, 1]});
same(colours.groups(), [[0, 1], [2]], 'apple colours are interchangeable');
same(colours.distinguish([1, 3, 2], [4, 0, 2]), null, 'merged counts suffice');
same(makeStudy(3, {}, {rate: [5, 5, 5]}).groups(), [[0, 1, 2]], 'uniform rate');
const prices = makeStudy(2, {}, {cost: [1, 2]});
same(prices.groups(), [[0], [1]], 'different unit prices');
same(prices.distinguish([2, 0], [0, 1]), null, 'different mixtures with equal cost');
same(makeStudy(2, {}, {}).groups(), [[0, 1]], 'empty observation set');
same(makeStudy(2, {}, {zero: [0, 0]}).probes.length, 0, 'rank zero');

// The determinant of the pair of readings is -1 even at this scale.
const n = 10n ** 30n;
const exact = makeStudy(2, {}, {one: [n, n + 1n], two: [n + 1n, n + 2n]});
same(exact.probes.length, 2, 'exact rank');
const diff = exact.distinguish([n + 1n, 0n], [0n, n]);
same([diff.reading, diff.leftValue - diff.rightValue], ['two', 1n], 'unit difference');
const signed = makeStudy(2, {}, {difference: [1, -1], twice: [2, -2]});
same(signed.probes.length, 1, 'dependent readings');
same(signed.read([0, 3], 'twice'), -6n, 'signed reading');

rejects(() => makeStudy(0, {}, {}), RangeError);
rejects(() => makeStudy(2, {bad: [[1, 0]]}, {}), RangeError);
rejects(() => makeStudy(2, {bad: [[1], [0, 1]]}, {}), RangeError);
rejects(() => makeStudy(1, {bad: [[-1]]}, {}), RangeError);
rejects(() => makeStudy(2, {}, {bad: [1]}), RangeError);
rejects(() => fruit.run([1, 2, 3], ['?']), RangeError);
rejects(() => fruit.read([1, 2, 3], '?'), RangeError);
rejects(() => fruit.run([1, -2, 0]), RangeError);
rejects(() => fruit.run([1, Number.MAX_SAFE_INTEGER + 1, 0]), TypeError);

console.log('PASS: ' + reconstructions + ' fruit orders reconstructed');
console.log('PASS: ' + menus + ' two-recipe menus, ' + comparisons + ' ordered stock pairs');
console.log('PASS: grouping, witness order, sharp bounds (d = 1..6), exact integers, input checks');
