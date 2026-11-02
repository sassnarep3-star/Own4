import { readFileSync, readdirSync, existsSync } from 'node:fs';
import assert from 'node:assert/strict';
import { impliedProbability, expectedReturn, correlation, jointHitRate, releaseGate } from '../docs/assets/engine.mjs';
const data = JSON.parse(readFileSync(new URL('../docs/data/catalog.json', import.meta.url)));
const sources = new Map(data.sources.map(s => [s.id,s]));
assert.equal(sources.size,data.sources.length);
for (const s of data.sources) {
  const u = new URL(s.url);
  assert.equal(u.protocol,'https:');
  assert.ok(u.hostname === 'nba.com' || u.hostname.endsWith('.nba.com'),s.url);
  assert.ok(s.checked && s.detail);
}
for (const group of ['strategies','gates','correlations','flags','requirements']) {
  const ids = new Set();
  for (const row of data[group]) {
    assert.ok(!ids.has(row.id),`duplicate ${row.id}`); ids.add(row.id);
    assert.ok(sources.has(row.source),`${row.id} missing official source`);
  }
}
for (const row of data.strategies) {
  assert.equal(row.output,''); assert.equal(row.correlation,''); assert.equal(row.status,'Research only');
}
for (const row of data.correlations) {
  assert.equal(row.estimate,''); assert.equal(row.interval,''); assert.equal(row.status,'Unverified');
}
assert.equal(impliedProbability(2),.5);
assert.equal(expectedReturn(.5,2),0);
assert.ok(Math.abs(expectedReturn(.4,2)+.2)<1e-12);
assert.ok(Math.abs(correlation([1,2,3],[3,2,1])+1)<1e-12);
assert.equal(correlation([1,1,1],[2,3,4]),null);
assert.equal(jointHitRate([[true,true],[true,false],[false,true],[false,false]]),.25);
assert.equal(releaseGate({}),false);
for (const page of ['index','strategies','validation','correlations','sources','flagged']) {
  const html = readFileSync(new URL(`../docs/${page}.html`,import.meta.url),'utf8');
  for (const local of [...html.matchAll(/(?:href|src)="([^"#?]+)"/g)].map(m=>m[1]).filter(x=>!x.startsWith('http'))) {
    assert.ok(existsSync(new URL(`../docs/${local}`,import.meta.url)),`${page}: broken ${local}`);
  }
}
console.log('Catalog provenance, blank unverified values, gate math and six page links: OK');
