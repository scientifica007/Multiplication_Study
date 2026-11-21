// Replay the archived calculators' own arithmetic. No browser or packages are needed.
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadArchive(filename) {
  const html = fs.readFileSync(path.join(__dirname, "..", "history", filename), "utf8");
  const core = html.match(/<script id="quantities-core">([\s\S]*?)<\/script>/);
  assert.ok(core, filename);
  return vm.runInNewContext(core[1] + "\nQuantities", {}, {filename});
}

function replayPlanar(q) {
  const read = q.parse;
  const amounts = new Set();
  let records = 0;
  for (let a = 1; a <= 12; a++) for (let k = 1; k <= 12; k++) {
    const left = read("apple(" + a + ")"), right = read("times(" + k + ")");
    const result = q.multiply(left, right);
    amounts.add(String(result.values[0]));
    const [first, second] = q.last(result).inputs;
    assert.ok(q.sameRecord(first, left) && q.sameRecord(second, right));
    records++;
  }
  assert.deepEqual([records, amounts.size], [144, 59]);
  const u = read("side(1,0)"), v = read("side(0,1)");
  assert.equal(q.add(u, v).kind, "side");
  assert.equal(q.multiply(u, v).kind, "area");
  assert.equal(q.add(read("apple(2)"), read("times(2)")).kind, "thing");
  assert.equal(q.multiply(read("apple(2)"), read("times(2)")).kind, "apple");
  const strips = [0, 0, 0]; // Equal magnitudes, unequal magnitudes, undefined net surface.
  let orientedEqual = 0;
  const moves = Array.from({length: 13}, (_, i) => i - 6).filter(x => x !== 0);
  for (const a of moves) for (const b of moves) {
    const first = read("side(" + a + ",0)"), second = read("side(" + b + ",0)");
    const separate = q.add(q.multiply(first, v), q.multiply(second, v));
    if (a + b === 0) {
      assert.throws(() => q.multiply(q.add(first, second), v), q.DomainError);
      strips[2]++;
    } else {
      const net = q.multiply(q.add(first, second), v);
      strips[q.sameReading(net, separate) ? 0 : 1]++;
      if (String(net.oriented) === String(separate.oriented)) orientedEqual++;
    }
  }
  assert.deepEqual(strips, [72, 60, 12]);
  assert.equal(orientedEqual, 132);
  const painted = read("(side(6,0)*side(0,1)) + (side(-2,0)*side(0,1))");
  assert.deepEqual([String(painted.oriented), String(painted.values[0]), String(q.coveredStrip(painted))], ["4", "8", "6"]);
  const hd = read("H*D"), dh = read("D*H");
  let different = 0;
  for (let x = -5; x <= 5; x++) for (let y = -5; y <= 5; y++) {
    const point = read("side(" + x + "," + y + ")");
    const same = q.sameReading(q.multiply(point, hd), q.multiply(point, dh));
    assert.equal(same, x === 0 && y === 0);
    if (!same) different++;
  }
  assert.equal(different, 120);
  console.log("144 histories / 59 counts; strips 72, 60, 12; projection order changes the endpoint for 120 of 121 input points.");
}

function replayCubes(q) {
  const lines = [0, 1, 2].flatMap(i => ["+", "-"].map(s => q.parse(s + "'".repeat(i) + "1")));
  const groups = new Map();
  let bases = 0, rejected = 0, recovered = 0;
  for (const a of lines) for (const b of lines) {
    let square;
    try { square = q.multiply(a, b); }
    catch (e) { if (e instanceof q.DomainError) continue; throw e; }
    bases++;
    for (const c of lines) {
      let cube;
      try { cube = q.multiply(square, c); }
      catch (e) { if (e instanceof q.DomainError) { rejected++; continue; } throw e; }
      const [base, last] = q.last(cube).inputs;
      const [first, second] = q.last(base).inputs;
      assert.ok(q.sameRecord(first, a) && q.sameRecord(second, b) && q.sameRecord(last, c));
      const key = cube.values.join(",");
      if (!groups.has(key)) groups.set(key, []);
      const group = groups.get(key);
      assert.ok(group.every(previous => !q.sameRecord(previous, cube)));
      group.push(cube);
      recovered++;
    }
  }
  assert.deepEqual([bases, rejected, recovered, groups.size], [24, 96, 48, 8]);
  assert.ok([...groups.values()].every(g => g.length === 6));
  assert.ok(q.sameRecord(q.parse("-+'1 * -1"), q.parse("-+-1")));
  assert.throws(() => q.parse("++1 * +1"), q.DomainError);
  console.log("24 ordered bases; 48 accepted and 96 rejected extensions; 8 cube positions, 6 histories each.");
}

for (const filename of ["quantity-history-lab-v1.html", "quantity-history-lab.html"]) {
  const q = loadArchive(filename);
  console.log(filename);
  replayPlanar(q);
  if (filename === "quantity-history-lab.html") replayCubes(q);
}
