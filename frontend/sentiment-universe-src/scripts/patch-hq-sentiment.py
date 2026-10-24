"""Bounded, idempotent FX-only patch for separately prepared HQ baseline copies.

Usage: python patch-hq-sentiment.py --main C:/candidate/frontend/src/app/main.js
No installer, backend, credentials, process control or full-file baseline replacement.
"""
from pathlib import Path
import argparse
import hashlib

HERE = Path(__file__).resolve().parent
MARKER = '// BEGIN SENTIMENT_UNIVERSE_HQ_V1'

def patch_display_and_focus(text):
    description='ดู Sentiment ชุมชน Myfxbook ความสัมพันธ์ราคาจาก MT5 และข่าว สำหรับ Forex 28 คู่ Metals 2 และ Oil 2 โดย Oil แสดงเมื่อมีข้อมูลที่ใช้ได้ ไม่มีการส่งคำสั่งเทรด'
    changes=[
        ('  left_signal_cube: "ศูนย์แนวโน้ม 28 คู่เงินและข่าว Forex",','  left_signal_cube: "Sentiment Universe · 32 สินทรัพย์",'),
        ('  left_signal_cube: { x: 24.2, y: 66.0, label: "ศูนย์แนวโน้ม 28 คู่เงินและข่าว Forex" },','  left_signal_cube: { x: 24.2, y: 66.0, label: "Sentiment Universe" },'),
        ('    labelTh: "FX BIAS CENTER",\n    eyebrowTh: "ภาพรวม 28 คู่เงิน ข่าว และช่วงเวลาที่ EA ควรระวัง",','    labelTh: "SENTIMENT UNIVERSE",\n    eyebrowTh: "Myfxbook Sentiment · MT5 Correlation · ปฏิทินข่าว",'),
        ('    [FX_NEWS_BIAS_PROP_ID]: "ติดตามข่าวและแนวโน้ม 28 คู่เงินในระยะสั้น กลาง และยาว พร้อมกำหนดเวลาอัปเดตข่าว โดยไม่ส่งคำสั่งเทรด",',f'    [FX_NEWS_BIAS_PROP_ID]: "{description}",'),
        ('  return state.propReports[subject.id]?.propertyRole || null;', '''  // SENTIMENT_UNIVERSE_COPY_V1: only display copy changes; retain role/backend IDs.
  const role = state.propReports[subject.id]?.propertyRole || null;
  return SENTIMENT_UNIVERSE_ENABLED && subject.id === FX_NEWS_BIAS_PROP_ID
    ? {...role,displayTitle: PROP_DISPLAY[FX_NEWS_BIAS_PROP_ID],purpose: getEquipmentPurpose(subject),openingMessage: "ข้อมูลตลาดแบบดูอย่างเดียวจาก Myfxbook, MT5 และปฏิทินข่าว"}
    : role;'''),
        ('function gameModalFocusableElements() {\n  if (!els.gameModal) return [];', '''function gameModalFocusableElements() {
  if (!els.gameModal) return [];
  // SENTIMENT_UNIVERSE_FOCUS_V1: this ShadowRoot has its own inner focus handling.
  if (SENTIMENT_UNIVERSE_ENABLED && state.modal.type === "prop" && state.modal.id === FX_NEWS_BIAS_PROP_ID) {
    const shadow = sentimentUniverseMount?.host?.shadowRoot;
    const nested = shadow ? [...shadow.querySelectorAll('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), [tabindex="0"]')] : [];
    return [els.modalCloseButton,els.workflowDashboardContent,...nested].filter((node) => node && !node.closest('[inert]') && node.getClientRects().length > 0);
  }'''),
    ]
    for old,new in changes:
        if text.count(old)==1 and new not in text:text=text.replace(old,new,1)
        elif text.count(new)!=1:raise ValueError('ambiguous_or_missing_display_anchor: '+old[:90])
    return text

def patch_text(text):
    if MARKER in text:
        if text.count(MARKER) != 1 or text.count('// SENTIMENT_UNIVERSE_HOOK') != 7:
            raise ValueError('partial_or_duplicate_sentiment_patch')
        return patch_display_and_focus(text)
    def insert(anchor, addition):
        nonlocal text
        if text.count(anchor) != 1:
            raise ValueError('ambiguous_or_missing_anchor: ' + anchor[:100])
        text = text.replace(anchor, anchor + addition, 1)
    insert('const FX_NEWS_BIAS_PROP_ID = "left_signal_cube";', '\n' + (HERE/'hq-embed-runtime.js').read_text(encoding='utf-8'))
    insert('function renderWorkflowDashboard(subject, propertyRole, report = {}) {', '''
  // SENTIMENT_UNIVERSE_HOOK: retain one mount across HQ report renders.
  if (SENTIMENT_UNIVERSE_ENABLED && subject?.id === FX_NEWS_BIAS_PROP_ID) {
    renderSentimentUniverse();
    return;
  }
''')
    insert('function openGameModal(type, id, tab = "chat") {', '''
  // SENTIMENT_UNIVERSE_HOOK: dispose only this equipment when switching away.
  if (type !== "prop" || id !== FX_NEWS_BIAS_PROP_ID) disposeSentimentUniverse();
''')
    insert('function closeGameModal() {', '''
  // SENTIMENT_UNIVERSE_HOOK: cancel its requests, RAF and WebGL resources.
  disposeSentimentUniverse();
''')
    insert('async function pollOpenPropReport({ force = false, signal = null } = {}) {', '''
  // SENTIMENT_UNIVERSE_HOOK: this equipment polls its read-only market mirror.
  if (SENTIMENT_UNIVERSE_ENABLED && state.modal.type === "prop" && state.modal.id === FX_NEWS_BIAS_PROP_ID) return null;
''')
    insert('async function loadPropReport(propId, { signal = null, forceFresh = false, shouldApply = null } = {}) {', '''
  // SENTIMENT_UNIVERSE_HOOK: retire legacy FX report reads only.
  if (SENTIMENT_UNIVERSE_ENABLED && propId === FX_NEWS_BIAS_PROP_ID) return state.propReports[propId] || null;
''')
    insert('async function saveFxNewsSchedule(form) {', '''
  // SENTIMENT_UNIVERSE_HOOK: legacy FX controls are replaced by local onboarding.
  if (SENTIMENT_UNIVERSE_ENABLED) return;
''')
    insert('async function refreshFxNewsDirect() {', '''
  // SENTIMENT_UNIVERSE_HOOK: no legacy FX refresh actions from the new screen.
  if (SENTIMENT_UNIVERSE_ENABLED) return;
''')
    return patch_display_and_focus(text)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    target=args.main.resolve()
    raw=target.read_bytes();bom=raw.startswith(b'\xef\xbb\xbf')
    text=raw.decode('utf-8-sig');newline='\r\n' if '\r\n' in text else '\n'
    patched=patch_text(text.replace('\r\n','\n')).replace('\n',newline)
    output=(b'\xef\xbb\xbf' if bom else b'')+patched.encode('utf-8')
    styles=target.parent.parent/'styles'/'sentiment-universe.css'
    if not args.check:
        target.write_bytes(output)
        styles.write_bytes((HERE/'hq-embed-layout.css').read_bytes())
    print(('Checked' if args.check else 'Patched') + ': ' + str(target))
    print('Before SHA256: '+hashlib.sha256(raw).hexdigest())
    print('After SHA256:  '+hashlib.sha256(output).hexdigest())

if __name__=='__main__':
    main()
