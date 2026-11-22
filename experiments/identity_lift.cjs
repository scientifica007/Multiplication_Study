'use strict';

// An inventory is a column. matrix[target][source] counts the outputs per unit.
function integer(value) {
  if (typeof value === 'bigint') return value;
  if (Number.isSafeInteger(value)) return BigInt(value);
  throw new TypeError('Use a safe integer or a bigint');
}

function vector(values, size, nonnegative) {
  if (!Array.isArray(values) || values.length !== size) {
    throw new RangeError('Wrong vector length');
  }
  return Array.from(values, value => {
    const n = integer(value);
    if (nonnegative && n < 0n) throw new RangeError('Negative quantity');
    return n;
  });
}

function dot(a, b) {
  return a.reduce((sum, v, i) => sum + v * b[i], 0n);
}

function gcd(a, b) {
  a = a < 0n ? -a : a;
  b = b < 0n ? -b : b;
  while (b !== 0n) [a, b] = [b, a % b];
  return a;
}

function primitive(row) {
  const divisor = row.reduce(gcd, 0n);
  return divisor > 1n ? row.map(v => v / divisor) : row;
}

// Fraction-free elimination over Q. Keep the actual probe in a separate list.
function addsRank(pivots, candidate) {
  let row = primitive(candidate);
  for (let i = 0; i < row.length; i++) {
    if (row[i] === 0n) continue;
    const pivot = pivots[i];
    if (!pivot) {
      pivots[i] = row;
      return true;
    }
    const a = pivot[i], b = row[i];
    row = primitive(row.map((v, j) => a * v - b * pivot[j]));
  }
  return false;
}

function makeStudy(size, recipes, readings) {
  if (!Number.isSafeInteger(size) || size < 1) throw new RangeError('Invalid size');
  const actions = new Map();
  for (const [name, matrix] of Object.entries(recipes)) {
    if (!Array.isArray(matrix) || matrix.length !== size) {
      throw new RangeError('Wrong matrix height');
    }
    actions.set(name, Array.from(matrix, row => vector(row, size, true)));
  }
  const outputs = new Map(Object.entries(readings).map(
    ([name, row]) => [name, vector(row, size, false)]
  ));

  const probes = [];
  const pivots = [];
  function consider(reading, steps, weights) {
    if (addsRank(pivots, weights)) {
      probes.push(Object.freeze({
        reading, steps: Object.freeze(steps), weights: Object.freeze(weights)
      }));
    }
  }
  for (const [name, row] of outputs) consider(name, [], row);
  // Prepend the new instruction: it is executed before the existing probe.
  for (let k = 0; k < probes.length; k++) {
    const {reading, steps, weights} = probes[k];
    for (const [name, matrix] of actions) {
      const next = weights.map((_, j) =>
        weights.reduce((sum, v, i) => sum + v * matrix[i][j], 0n)
      );
      consider(reading, [name, ...steps], next);
    }
  }

  function run(stock, steps = []) {
    let current = vector(stock, size, true);
    for (const name of steps) {
      if (!actions.has(name)) throw new RangeError('Unknown instruction: ' + name);
      current = actions.get(name).map(row => dot(row, current));
    }
    return current;
  }

  function read(stock, reading, steps = []) {
    if (!outputs.has(reading)) throw new RangeError('Unknown reading: ' + reading);
    return dot(outputs.get(reading), run(stock, steps));
  }

  function distinguish(left, right) {
    const x = vector(left, size, true), y = vector(right, size, true);
    for (const {reading, steps, weights} of probes) {
      const leftValue = dot(weights, x), rightValue = dot(weights, y);
      if (leftValue !== rightValue) return {reading, steps, leftValue, rightValue};
    }
    return null;
  }

  function groups() {
    const byColumn = new Map();
    for (let j = 0; j < size; j++) {
      const signature = probes.map(({weights}) => weights[j].toString()).join(',');
      if (!byColumn.has(signature)) byColumn.set(signature, []);
      byColumn.get(signature).push(j);
    }
    return [...byColumn.values()];
  }

  return {probes: Object.freeze(probes), run, read, distinguish, groups};
}

function fruitStudy() {
  // Coordinate order: unmarked apple, pear, marked apple.
  return makeStudy(3, {
    S: [[0, 0, 0], [0, 1, 0], [1, 0, 1]],
    D: [[1, 0, 0], [0, 1, 0], [0, 0, 2]]
  }, {total: [1, 1, 1]});
}

module.exports = {makeStudy, fruitStudy};

if (require.main === module) {
  const study = fruitStudy();
  const left = [3, 1, 0], right = [1, 3, 0];
  for (const steps of [[], ['S'], ['D'], ['D', 'S'], ['S', 'D']]) {
    const totals = [left, right].map(order => String(study.read(order, 'total', steps)));
    console.log((steps.join(' → ') || 'البداية') + ' | ' + totals.join(' ، '));
  }
  for (const {steps, weights} of study.probes) {
    console.log((steps.join(' → ') || 'البداية') + ' | (' + weights.join(', ') + ')');
  }
}
