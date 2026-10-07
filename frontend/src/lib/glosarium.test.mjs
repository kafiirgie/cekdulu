import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const baca = (p) => readFileSync(new URL(p, import.meta.url), 'utf8')

const glosarium = JSON.parse(baca('../../../contract/glosarium.json'))
const kunci = glosarium.istilah.map((i) => i.key)
const schemaPy = baca('../../../backend/app/schemas.py')
const contractTs = baca('./contract.ts')

/** Kunci dari blok `GlosariumKey = Literal[...]` di schemas.py. */
const kunciPy = [...(/GlosariumKey = Literal\[([\s\S]*?)\]/.exec(schemaPy)?.[1] ?? '').matchAll(/"([a-z_]+)"/g)].map((m) => m[1])
/** Kunci dari `export type KunciGlosarium = ...` di contract.ts. */
const kunciTs = [...(/export type KunciGlosarium =([\s\S]*?)(?=\n\n|$)/.exec(contractTs)?.[1] ?? '').matchAll(/'([a-z_]+)'/g)].map((m) => m[1])

const sama = (a, b) => JSON.stringify([...a].sort()) === JSON.stringify([...b].sort())

test('kontrak: glosarium.json, schemas.py, dan contract.ts memuat kunci yang sama', () => {
  assert.ok(kunci.length >= 10, 'glosarium.json terlalu pendek')
  assert.equal(new Set(kunci).size, kunci.length, 'ada kunci kembar di glosarium.json')
  assert.ok(sama(kunci, kunciPy), 'kunci di schemas.py tidak sama dengan glosarium.json')
  assert.ok(sama(kunci, kunciTs), 'kunci di contract.ts tidak sama dengan glosarium.json')
})

test('kontrak: setiap entri glosarium punya nama dan arti', () => {
  for (const i of glosarium.istilah) {
    assert.ok(i.nama?.trim() && i.arti?.trim(), `entri tanpa nama/arti: ${i.key}`)
  }
})
