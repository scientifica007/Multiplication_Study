'use strict';

const {makeStudy, fruitRecipes, recipeMatrices, vector, dot} = require('./identity_lift.cjs');

// All residues are possible starting stocks. A separate last state denotes failure.
function minimizeAdmission(table) {
  const sink = table.length - 1;
  let labels = table.map((_, i) => Number(i === sink));
  let count = 2;
  for (;;) {
    const ids = new Map();
    const next = table.map((targets, state) => {
      const signature = [labels[state], ...targets.map(t => labels[t])].join(',');
      if (!ids.has(signature)) ids.set(signature, ids.size);
      return ids.get(signature);
    });
    labels = next;
    if (ids.size === count) break;
    count = ids.size;
  }
  const transitions = [];
  table.forEach((targets, i) => {
    if (!transitions[labels[i]]) transitions[labels[i]] = targets.map(t => labels[t]);
  });
  return {labels, transitions, sink: labels[sink]};
}

function makeGuardedStudy(size, modulus, recipes, guards, readings) {
  const matrices = recipeMatrices(size, recipes);
  if (!Number.isSafeInteger(modulus) || modulus < 1) throw new RangeError('Invalid modulus');
  const residueCount = modulus ** size;
  if (!Number.isSafeInteger(residueCount) || residueCount >= 0xffffffff) {
    throw new RangeError('Residue table exceeds the JavaScript array size');
  }
  const checks = new Map(Object.entries(guards));
  for (const [name, test] of checks) {
    if (!matrices.has(name)) throw new RangeError('Guard for unknown instruction: ' + name);
    if (typeof test !== 'function') throw new TypeError('Expected a residue predicate');
  }
  const outputs = Object.entries(readings).map(([name, row]) => [name, vector(row, size, false)]);
  const names = [...matrices.keys()];
  const columns = new Map(names.map((name, j) => [name, j]));
  const m = BigInt(modulus);
  function residueIndex(stock) {
    return stock.reduceRight((code, v) => code * modulus + Number(v % m), 0);
  }
  const table = Array.from({length: residueCount}, (_, index) => {
    const digits = Array.from({length: size}, () => {
      const digit = index % modulus;
      index = Math.floor(index / modulus);
      return BigInt(digit);
    });
    Object.freeze(digits);
    return names.map(name => {
      const allowed = checks.has(name) ? checks.get(name)(digits) : true;
      if (typeof allowed !== 'boolean') throw new TypeError('Guard must return a boolean');
      if (!allowed) return residueCount;
      return residueIndex(matrices.get(name).map(row => dot(row, digits)));
    });
  });
  table.push(names.map(() => residueCount));
  const {labels, transitions, sink} = minimizeAdmission(table);
  // Class IDs are assigned in residue order, before the one failure state.
  const classCount = transitions.length - 1;
  function classOf(stock) {
    return labels[residueIndex(vector(stock, size, true))];
  }

  function admissionWitness(left, right) {
    const a = classOf(left), b = classOf(right);
    if (a === b) return null;
    const pending = [{a, b, steps: []}];
    const seen = new Set([a + ',' + b]);
    for (let i = 0; i < pending.length; i++) {
      const current = pending[i];
      for (let j = 0; j < names.length; j++) {
        const p = transitions[current.a][j], q = transitions[current.b][j];
        if (p === q || seen.has(p + ',' + q)) continue;
        const steps = [...current.steps, names[j]];
        if (p === sink || q === sink) return {steps, left: p !== sink, right: q !== sink};
        seen.add(p + ',' + q);
        pending.push({a: p, b: q, steps});
      }
    }
    throw new Error('Distinct admission classes have no witness');
  }

  function observe(stock, steps = []) {
    let x = vector(stock, size, true);
    let state = labels[residueIndex(x)];
    for (const name of steps) {
      if (!columns.has(name)) throw new RangeError('Unknown instruction: ' + name);
      state = transitions[state][columns.get(name)];
      if (state === sink) return null;
      x = matrices.get(name).map(row => dot(row, x));
    }
    return Object.fromEntries(outputs.map(([name, row]) => [name, dot(row, x)]));
  }

  // A valid stock has just one active block (1, x). A rejected prefix has none.
  const stride = size + 1, width = stride * classCount;
  function encode(stock) {
    const x = vector(stock, size, true);
    const start = stride * labels[residueIndex(x)];
    const encoded = Array(width).fill(0n);
    encoded[start] = 1n;
    x.forEach((v, i) => { encoded[start + i + 1] = v; });
    return encoded;
  }
  function comparisonStudy() {
    const blocks = Object.fromEntries(names.map((name, j) => {
      const matrix = Array.from({length: width}, () => Array(width).fill(0n));
      const action = matrices.get(name);
      for (let source = 0; source < classCount; source++) {
        const target = transitions[source][j];
        if (target === sink) continue;
        const from = source * stride, to = target * stride;
        matrix[to][from] = 1n;
        for (let i = 0; i < size; i++) {
          for (let k = 0; k < size; k++) matrix[to + 1 + i][from + 1 + k] = action[i][k];
        }
      }
      return [name, matrix];
    }));
    const repeat = row => Array.from({length: classCount}, () => row).flat();
    const blockReadings = {admitted: repeat([1n, ...Array(size).fill(0n)])};
    outputs.forEach(([, row], i) => { blockReadings['v' + i] = repeat([0n, ...row]); });
    return makeStudy(width, blocks, blockReadings);
  }
  let linear;
  function distinguish(left, right) {
    let witness;
    if (outputs.length) {
      linear ??= comparisonStudy();
      witness = linear.distinguish(encode(left), encode(right));
    } else {
      witness = admissionWitness(left, right);
    }
    if (!witness) return null;
    const {steps} = witness;
    return {steps, left: observe(left, steps), right: observe(right, steps)};
  }
  return {classCount, classOf, observe, admissionWitness, distinguish};
}

function guardedFruit() {
  const G = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  return makeGuardedStudy(3, 2, {...fruitRecipes(), G},
    {G: ([a, , t]) => (a + t) % 2n === 0n}, {total: [1, 1, 1]});
}

module.exports = {makeGuardedStudy, guardedFruit};

if (require.main === module) {
  const study = guardedFruit();
  console.log('فئات الطلبيات اللازمة للجواز: ' + study.classCount);
  console.log('غير موسوم، إجاص، موسوم | الفحص | العدد بعد المضاعفة | الفحص بعد المضاعفة');
  for (const stock of [[2, 2, 0], [1, 2, 1], [0, 2, 2]]) {
    const gate = steps => study.observe(stock, steps) === null ? 'رفض' : 'قبول';
    const total = study.observe(stock, ['D']).total;
    console.log(['(' + stock.join(', ') + ')', gate(['G']), total, gate(['D', 'G'])].join(' | '));
  }
}
