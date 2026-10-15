import test from 'node:test';
import assert from 'node:assert/strict';
import {escapeHtml,readableError,validateQuestion,formatElapsed,safeApiUrl} from '../web/utils.mjs';

test('escapes untrusted document passages and generated HTML',()=>{
  assert.equal(escapeHtml('<img src=x onerror="evil()">'), '&lt;img src=x onerror=&quot;evil()&quot;&gt;');
});
test('rejects blank questions',()=>assert.throws(()=>validateQuestion('  ',3),/Enter/));
test('accepts valid questions and trims whitespace',()=>assert.deepEqual(validateQuestion(' What is required? ',2),{question:'What is required?',top_k:2}));
test('limits retrieval depth',()=>assert.throws(()=>validateQuestion('Question',11),/depth/));
test('formats elapsed time',()=>assert.equal(formatElapsed(72.3),'01:12'));
test('recognises expired document workspace',()=>assert.match(readableError(404,'Document workspace not found or expired'),/index the documents again/));
test('blocks javascript, http public URLs and embedded credentials',()=>{
  assert.equal(safeApiUrl('javascript:alert(1)'),null);
  assert.equal(safeApiUrl('http://unsafe.example.com'),null);
  assert.equal(safeApiUrl('https://user:password@example.com'),null);
  assert.equal(safeApiUrl('https://demo.onrender.com/foo'),'https://demo.onrender.com');
  assert.equal(safeApiUrl('http://127.0.0.1:8000'),'http://127.0.0.1:8000');
});
