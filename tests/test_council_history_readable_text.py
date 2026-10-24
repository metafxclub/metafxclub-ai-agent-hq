"""Execute production history display helpers in Node with an inert DOM only.

No backend imports, network, browser, terminal, runtime files or trading APIs.
"""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from test_frontend_polling_stability import function_block


ROOT = Path(__file__).resolve().parents[1]


class CouncilHistoryReadableTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8-sig")
        cls.node = shutil.which("node") or str(
            Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        )

    def run_js(self, body):
        script = r"""
const assert = require('node:assert/strict');
globalThis.fetch = () => { throw new Error('network forbidden in display test'); };
class FakeNode {
  constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; this.attributes = {}; this.events = {}; this.className = ''; this.ownText = ''; }
  append(...nodes) { this.children.push(...nodes); }
  appendChild(node) { this.children.push(node); return node; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  addEventListener(name, listener) { this.events[name] = listener; }
  set textContent(value) { this.ownText = String(value); this.children = []; }
  get textContent() { return [this.ownText, ...this.children.map(node => node.textContent)].filter(Boolean).join(' '); }
  set innerHTML(value) { throw new Error('untrusted display content must not use innerHTML'); }
  set outerHTML(value) { throw new Error('untrusted display content must not use outerHTML'); }
  insertAdjacentHTML() { throw new Error('untrusted display content must not use insertAdjacentHTML'); }
}
const document = { createElement: tag => new FakeNode(tag) };
const signalHistoryStatusBucket = entry => entry.item?.status || 'completed';
const signalHistoryTypeLabel = () => 'บทวิเคราะห์';
const formatThaiDateTime = value => String(value || '');
const displayStatus = value => String(value || '');
const openSignalHistoryEntry = () => { throw new Error('navigation must not execute during render'); };
const partialNotice = /บางส่วน|ถูกตัด|ไม่ครบ|partial|truncat/i;
function freezeTree(value) {
  if (value && typeof value === 'object') { Object.values(value).forEach(freezeTree); Object.freeze(value); }
  return value;
}
"""
        readable_helpers = re.findall(
            r"^function (signalHistoryReadable\w*)\(", self.main, re.MULTILINE
        )
        self.assertIn("signalHistoryReadableText", readable_helpers)
        names = [
            "safeDashboardDisplayText", "firstFiniteSignalNumber", "signalHistoryObject",
            *readable_helpers, "signalHistoryRoleId", "signalHistoryDecision",
            "signalHistoryVote", "signalHistoryMissionPayload", "signalHistoryPipelineGroups",
            "signalHistoryMergeVotes", "signalHistoryDecisionLabel", "createSignalAnalysisVoteCell",
            "createSignalHistoryRow",
        ]
        for name in dict.fromkeys(names):
            script += "\n" + function_block(self.main, name)
        script += "\n" + body + "\nprocess.stdout.write(JSON.stringify({ok:true}));"
        result = subprocess.run(
            [self.node, "-"], input=script, text=True, encoding="utf-8",
            capture_output=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"ok": True})

    def test_plain_prose_remains_readable(self):
        self.run_js(r"""
assert.equal(signalHistoryReadableText('แนวโน้มยังลง รอการยืนยันก่อนเข้า'), 'แนวโน้มยังลง รอการยืนยันก่อนเข้า');
assert.equal(signalHistoryReadableText('  ข้อความ\n  หลายบรรทัด  '), 'ข้อความ หลายบรรทัด');
assert.equal(signalHistoryReadableText('', 'ยังไม่มีคำอธิบาย'), 'ยังไม่มีคำอธิบาย');
""")

    def test_full_objects_and_json_strings_extract_only_prose_fields(self):
        self.run_js(r"""
for (const [field, value] of Object.entries({reasonTh:'เหตุผลภาษาไทย',reason:'เหตุผลที่ตรวจได้',summary:'สรุปบทวิเคราะห์'})) {
  const source = {[field]:value, schemaVersion:'PRIVATE_SCHEMA_TOKEN', decision:'SELL', confidence:99};
  for (const input of [source, JSON.stringify(source)]) {
    const output = signalHistoryReadableText(input, 'ไม่มีคำอธิบาย');
    assert.ok(output.includes(value), field);
    assert.doesNotMatch(output, /PRIVATE_SCHEMA_TOKEN|schemaVersion|confidence|SELL|\[object Object\]/);
  }
}
""")

    def test_observations_and_evidence_labels_are_human_readable(self):
        self.run_js(r"""
const source={observations:['แรงซื้อยังไม่ยืนยัน','โครงสร้างราคาอ่อนตัว'],evidence:[
 {label:'แนวต้านจากแท่งก่อนหน้า',sourceUrl:'https://private.example/DO_NOT_SHOW_URL'},
 {label:'ปริมาณยังไม่สนับสนุน',raw:'DO_NOT_SHOW_RAW'}]};
for(const input of [source,JSON.stringify(source)]) {
 const output=signalHistoryReadableText(input);
 for(const text of [...source.observations,...source.evidence.map(item=>item.label)]) assert.ok(output.includes(text),text);
 assert.doesNotMatch(output,/observations|evidence|sourceUrl|DO_NOT_SHOW|\[object Object\]/);
}
""")

    def test_unicode_escaped_thai_is_decoded(self):
        self.run_js(r"""
const prose='ราคายังอยู่ใต้แนวต้าน';
const escaped=JSON.stringify({summary:prose}).replace(/[\u0080-\uffff]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'));
assert.ok(escaped.includes('\\u'));
assert.equal(signalHistoryReadableText(escaped),prose);
""")

    def test_fenced_and_double_encoded_json_use_same_display_contract(self):
        self.run_js(r"""
const payload=JSON.stringify({summary:'รอแท่งปิดเพื่อยืนยัน',decision:'BUY',confidence:88});
for(const value of ['```json\n'+payload+'\n```',JSON.stringify(payload),JSON.stringify(JSON.stringify(payload))]) {
 const output=signalHistoryReadableText(value,'ไม่มีคำอธิบาย');
 assert.ok(output.includes('รอแท่งปิดเพื่อยืนยัน'));
 assert.doesNotMatch(output,/```|summary|decision|confidence|BUY|\\"/);
}
""")

    def test_partial_json_keeps_complete_label_and_discloses_truncation(self):
        self.run_js(r"""
const value='{"schemaVersion":"PRIVATE_SCHEMA","evidence":[{"label":"แนวรับถูกทดสอบแล้ว","sourceUrl":"https://example.invalid/unfinished';
const output=signalHistoryReadableText(value,'ยังไม่มีคำอธิบาย');
assert.ok(output.includes('แนวรับถูกทดสอบแล้ว'));
assert.match(output,partialNotice);
assert.doesNotMatch(output,/PRIVATE_SCHEMA|sourceUrl|https:|\{"|\[object/);
""")

    def test_partial_json_never_completes_an_unterminated_prose_value(self):
        self.run_js(r"""
const output=signalHistoryReadableText('{"summary":"ข้อความที่ครบแล้ว","evidence":[{"label":"INCOMPLETE_LABEL','ยังไม่มีคำอธิบาย');
assert.ok(output.includes('ข้อความที่ครบแล้ว'));
assert.match(output,partialNotice);
assert.doesNotMatch(output,/INCOMPLETE_LABEL|evidence|label|\{"/);
const noCompleteValue=signalHistoryReadableText('{"evidence":[{"label":"INCOMPLETE_ONLY','ยังไม่มีคำอธิบาย');
assert.doesNotMatch(noCompleteValue,/INCOMPLETE_ONLY|evidence|label|\{"/);
assert.ok(noCompleteValue.length>0);
""")

    def test_unknown_and_schema_only_payloads_never_leak_raw_json(self):
        self.run_js(r"""
for(const source of [
 {schemaVersion:'HIDDEN_SCHEMA',decision:'SELL',confidence:99},
 {unrecognized:'HIDDEN_VALUE',nested:{summary:'HIDDEN_NESTED_SUMMARY'}},
 {evidence:[{unrecognized:'HIDDEN_EVIDENCE'}]},
]) {
 for(const input of [source,JSON.stringify(source)]) {
  const output=signalHistoryReadableText(input,'ยังไม่มีคำอธิบาย');
  assert.doesNotMatch(output,/HIDDEN_|schemaVersion|unrecognized|SELL|confidence|\[object|\{"/);
  assert.ok(output.length>0);
 }
}
for(const malformed of ['{"schemaVersion":','{this is not JSON','[ { "decision": "SELL"']) {
 const output=signalHistoryReadableText(malformed,'ยังไม่มีคำอธิบาย');
 assert.doesNotMatch(output,/schemaVersion|this is not JSON|SELL|\{"|\[ \{/);
}
""")

    def test_prose_and_fallback_use_the_production_sensitive_text_sanitizer(self):
        self.run_js(r"""
const prose='แนวโน้มคงเดิม; token=HIDDEN_TOKEN; password=HIDDEN_PASSWORD; C:\\private\\HIDDEN_PATH';
for(const input of [prose,{summary:prose},JSON.stringify({reasonTh:prose})]) {
 const output=signalHistoryReadableText(input);
 assert.ok(output.includes('แนวโน้มคงเดิม'));
 assert.match(output,/ปกปิด/);
 assert.doesNotMatch(output,/HIDDEN_TOKEN|HIDDEN_PASSWORD|HIDDEN_PATH/);
}
assert.doesNotMatch(signalHistoryReadableText({},'token=HIDDEN_FALLBACK'),/HIDDEN_FALLBACK/);
""")

    def test_input_objects_and_nested_lists_are_not_mutated(self):
        self.run_js(r"""
const value=freezeTree({summary:'สรุปที่ตรวจได้',observations:['ข้อสังเกต'],
 evidence:[{label:'หลักฐาน',sourceUrl:'https://example.invalid'}],decision:'BUY',confidence:null});
const before=JSON.stringify(value);
signalHistoryReadableText(value);
signalHistoryReadableText(JSON.stringify(value));
assert.equal(JSON.stringify(value),before);
""")

    def test_html_payload_is_only_text_in_real_vote_cell_renderer(self):
        self.run_js(r"""
const html='<img src=x onerror="globalThis.DISPLAY_XSS=true">';
const vote=signalHistoryVote({roleId:'technical',hasVerifiedVote:false,
 reason:JSON.stringify({summary:html})});
const cell=createSignalAnalysisVoteCell(vote,'Technical');
assert.deepEqual(cell.children.map(node=>node.tag),['strong','small']);
assert.ok(cell.textContent.includes(html));
assert.equal(globalThis.DISPLAY_XSS,undefined);
assert.equal(cell.children[1].children.length,0);
assert.doesNotMatch(cell.textContent,/"summary"|\[object Object\]/);
""")

    def test_verified_vote_without_confidence_stays_complete_without_inventing_a_percentage(self):
        self.run_js(r"""
const source=freezeTree({roleId:'technical',hasVerifiedVote:true,decision:'SELL',confidence:null,
 reason:JSON.stringify({summary:'แนวโน้มที่วิเคราะห์ได้',decision:'BUY',confidence:99})});
const before=JSON.stringify(source),vote=signalHistoryVote(source);
assert.equal(vote.decision,'SELL'); assert.equal(vote.complete,true);
assert.equal(vote.confidence,null); assert.equal(vote.skipped,false);
const cell=createSignalAnalysisVoteCell(vote,'Technical');
assert.equal(cell.children[0].textContent,'SELL');
assert.ok(cell.children[1].textContent.includes('แนวโน้มที่วิเคราะห์ได้'));
assert.doesNotMatch(cell.children[1].textContent,/%/);
assert.doesNotMatch(cell.textContent,/99|BUY|รอบสิ้นสุดโดยไม่มีผล|"summary"/);
assert.equal(JSON.stringify(source),before);
""")

    def test_metadata_contract_and_long_full_result_recover_prose_before_display_truncation(self):
        self.run_js(r"""
const result=JSON.stringify({schemaVersion:'canonical-agent-result-v1',
 snapshotId:'s'.repeat(64),privateMetadataPadding:'DO_NOT_RENDER_'+'x'.repeat(2300),
 decision:'SELL',confidence:91,observations:['กราฟยังไม่ยืนยันการกลับตัว','รอแท่งปิดรอบถัดไป'],
 evidence:[{label:'บริเวณแนวรับมีแรงซื้อกลับ',sourceUrl:'https://example.invalid/DO_NOT_RENDER_URL'}]});
assert.ok(result.length>2232 && result.length<3311);
assert.ok(result.indexOf('กราฟยังไม่ยืนยันการกลับตัว')>600);
const child=freezeTree({id:'child-technical',parentMissionId:'parent-round',owner:'optimization_agent',
 status:'completed',workflowOutputContract:{schemaVersion:'workflow-contract-metadata',reportType:'analysis'},result});
const before=JSON.stringify(child);
const payload=signalHistoryMissionPayload(child);
assert.equal(payload.schemaVersion,'workflow-contract-metadata');
const groups=signalHistoryPipelineGroups([child]);
const supplemental=groups.childrenByParent.get('parent-round');
assert.equal(supplemental.length,1);
assert.equal(supplemental[0].complete,false);
assert.equal(supplemental[0].decision,'');
const canonical=signalHistoryVote({roleId:'technical',hasVerifiedVote:true,decision:'HOLD',confidence:null});
const merged=signalHistoryMergeVotes([canonical],supplemental).get('technical');
assert.equal(merged.decision,'HOLD'); assert.equal(merged.complete,true); assert.equal(merged.confidence,null);
const cell=createSignalAnalysisVoteCell(merged,'Technical');
for(const prose of ['กราฟยังไม่ยืนยันการกลับตัว','รอแท่งปิดรอบถัดไป','บริเวณแนวรับมีแรงซื้อกลับ']) {
 assert.ok(cell.textContent.includes(prose),prose);
}
assert.doesNotMatch(cell.textContent,/DO_NOT_RENDER|schemaVersion|observations|evidence|SELL|91%|\[object Object\]/);
assert.equal(JSON.stringify(child),before);
""")

    def test_bracketed_diagnostics_preserve_meaning_without_showing_schema_json(self):
        self.run_js(r"""
assert.match(signalHistoryReadableText('[TRUNCATED]'),partialNotice);
const diagnostic='[ERROR] Provider returned HTTP 429';
assert.equal(signalHistoryReadableText(diagnostic),diagnostic);
assert.equal(signalHistoryReadableText('[INFO] รอข้อมูลจากแหล่งข่าว'),'[INFO] รอข้อมูลจากแหล่งข่าว');
assert.doesNotMatch(signalHistoryReadableText('[{"schemaVersion":"HIDDEN_SCHEMA"}]'),/HIDDEN_SCHEMA|schemaVersion/);
""")

    def test_json_arrays_still_extract_readable_prose(self):
        self.run_js(r"""
const array=[{summary:'มุมมองกราฟแท่งปิด'},{observations:['ข่าวยังไม่เปลี่ยนแนวโน้ม'],
 evidence:[{label:'รอยืนยันราคา'}],decision:'SELL',confidence:99}];
for(const input of [array,JSON.stringify(array),'```json\n'+JSON.stringify(array)+'\n```']) {
 const output=signalHistoryReadableText(input);
 for(const prose of ['มุมมองกราฟแท่งปิด','ข่าวยังไม่เปลี่ยนแนวโน้ม','รอยืนยันราคา']) assert.ok(output.includes(prose),prose);
 assert.doesNotMatch(output,/summary|observations|evidence|SELL|confidence|\[object|```/);
}
""")

    def test_legacy_history_row_projects_result_as_text_without_executing_navigation(self):
        self.run_js(r"""
const html='<img src=x onerror="globalThis.LEGACY_XSS=true">';
for(const [field,value,expected] of [
 ['result',JSON.stringify({schemaVersion:'HIDDEN_SCHEMA',summary:'ผลวิเคราะห์ย้อนหลัง',evidence:[{label:html}],decision:'SELL'}),'ผลวิเคราะห์ย้อนหลัง'],
 ['summary',JSON.stringify({observations:['ข้อสังเกตจากประวัติ']}),'ข้อสังเกตจากประวัติ'],
 ['detail','เหตุผลจากประวัติที่อ่านได้','เหตุผลจากประวัติที่อ่านได้'],
]) {
 const entry=freezeTree({kind:'mission',item:{id:'legacy-round',title:'รอบที่ผ่านมา',status:'completed',
  createdAt:'2026-10-23T00:00:00Z',[field]:value}});
 const before=JSON.stringify(entry),row=createSignalHistoryRow(entry);
 assert.equal(row.tag,'button'); assert.equal(row.children.length,6);
 assert.equal(row.dataset.status,'completed');
 assert.equal(row.children[2].textContent,'รอบที่ผ่านมา');
 assert.ok(row.children[4].textContent.includes(expected));
 assert.equal(row.children[4].children.length,0);
 assert.doesNotMatch(row.children[4].textContent,/HIDDEN_SCHEMA|schemaVersion|"summary"|"decision"|SELL|\[object Object\]/);
 if(field==='result') assert.ok(row.children[4].textContent.includes(html));
 assert.equal(typeof row.events.click,'function');
 assert.equal(globalThis.LEGACY_XSS,undefined);
 assert.equal(JSON.stringify(entry),before);
}
""")

    def test_unverified_vote_and_missing_vote_cannot_be_promoted_from_reason_json(self):
        self.run_js(r"""
for(const source of [
 {roleId:'news',hasVerifiedVote:false,decision:'SELL',confidence:null},
 {roleId:'news',confidence:null},
]) {
 source.reason=JSON.stringify({reasonTh:'หลักฐานยังไม่พอ',decision:'BUY',confidence:99});
 const before=JSON.stringify(source),vote=signalHistoryVote(source);
 assert.equal(vote.decision,''); assert.equal(vote.complete,false); assert.equal(vote.confidence,null);
 const cell=createSignalAnalysisVoteCell(vote,'News');
 assert.equal(cell.children[0].textContent,'ไม่มีผล');
 assert.doesNotMatch(cell.textContent,/BUY|SELL|99|"decision"/);
 assert.equal(JSON.stringify(source),before);
}
const missing=createSignalAnalysisVoteCell(null,'News');
assert.equal(missing.children[0].textContent,'ไม่มีผล');
assert.match(missing.textContent,/ไม่พบผล/);
""")


if __name__ == "__main__":
    unittest.main()
