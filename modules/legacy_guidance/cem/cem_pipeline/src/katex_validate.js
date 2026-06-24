// Batch KaTeX structural-validity gate.
// Reads a JSON file {id: latex, ...} and writes {id: bool, ...} to stdout.
// A latex string is "valid" iff katex.renderToString(...) does not throw.
const fs = require('fs');
let katex;
try { katex = require('katex'); }
catch (e) {
  process.stderr.write('FATAL: katex not installed (run `npm install katex`)\n');
  process.exit(2);
}
const inPath = process.argv[2];
let d;
try { d = JSON.parse(fs.readFileSync(inPath, 'utf8').replace(/^﻿/, '')); }
catch (e) { process.stderr.write('FATAL: cannot read input JSON: ' + e + '\n'); process.exit(3); }
const out = {};
for (const [id, latex] of Object.entries(d)) {
  try {
    katex.renderToString(String(latex), { throwOnError: true, displayMode: true, strict: false });
    out[id] = true;
  } catch (e) {
    out[id] = false;
  }
}
process.stdout.write(JSON.stringify(out));
