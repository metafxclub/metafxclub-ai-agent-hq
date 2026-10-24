const $ = selector => document.querySelector(selector);
let saving = false, choosing = false, polling = false, discoveryRevision = '', firstSetup = true;
const messages = {
 needs_configuration:'ยังไม่ได้เชื่อมบัญชี', ready:'เชื่อมต่อสำเร็จ', ok:'เชื่อมต่อสำเร็จ', fresh:'เชื่อมต่อสำเร็จ',
 auth_error:'Myfxbook ไม่ยอมรับข้อมูลเข้าสู่ระบบ กรุณาตรวจบัญชี', auth_failed:'Myfxbook ไม่ยอมรับข้อมูลเข้าสู่ระบบ กรุณาตรวจบัญชี',
 rate_limited:'ถึงขีดจำกัดของแหล่งข้อมูล ระบบจะรอรอบถัดไป', stale:'กำลังแสดงข้อมูลรอบก่อนระหว่างรออัปเดต',
 partial:'เชื่อมแล้ว มีข้อมูลบางสินทรัพย์', unavailable:'ยังไม่มีข้อมูลที่พร้อมใช้งาน', loading:'กำลังตรวจการเชื่อมต่อ',
 provider_unavailable:'แหล่งข้อมูลยังไม่ตอบข้อมูลที่ใช้ได้ ระบบจะลองใหม่ตามรอบ',
 verifying:'กำลังตรวจ MT5 และเวลาโบรกเกอร์', verifying_selected_terminal:'กำลังตรวจ MT5 ที่เลือก',
 waiting_for_live_ticks:'บันทึก MT5 แล้ว รอราคาใหม่เพื่อยืนยันเวลาโบรกเกอร์อัตโนมัติ',
 clock_unverified:'รอราคาใหม่เพื่อยืนยันเวลาโบรกเกอร์', unverified_clock:'รอราคาใหม่เพื่อยืนยันเวลาโบรกเกอร์',
 terminal_not_running:'MT5 ที่เลือกยังไม่เปิด กรุณาเปิด MT5 เดิม ระบบจะตรวจพบเอง',
 terminal_closed:'MT5 ที่เลือกยังไม่เปิด กรุณาเปิด MT5 เดิม ระบบจะตรวจพบเอง',
 terminal_disconnected:'MT5 ยังไม่เชื่อมเซิร์ฟเวอร์โบรกเกอร์', not_selected:'ยังไม่ได้เลือก MT5 สำหรับหน้าดาว',
 selection_not_saved:'ยังบันทึกการเลือกไม่ได้ กรุณาค้นหาใหม่', stale_discovery:'รายการ MT5 เปลี่ยนแล้ว กรุณาค้นหาใหม่',
 candidate_unavailable:'MT5 นี้ยังไม่พร้อม กรุณาค้นหาใหม่', candidate_not_found:'ไม่พบ MT5 ที่เลือก กรุณาค้นหาใหม่',
 discovery_expired:'รายการ MT5 หมดอายุ กรุณาค้นหาใหม่', invalid_selection:'ข้อมูลการเลือกไม่ถูกต้อง กรุณาค้นหาใหม่',
 data_path_ambiguous:'พบหลายโฟลเดอร์ข้อมูลของ MT5 นี้ ต้องตรวจโฟลเดอร์ก่อนเชื่อม',
 market_closed:'ตลาดปิด แสดงแท่งล่าสุดที่ปิดแล้ว', empty:'ไม่มีข่าวตามปฏิทินที่ครอบคลุมวันนี้',
 error:'ยังอัปเดตไม่สำเร็จ ระบบจะตรวจใหม่ตามรอบ'
};
Object.assign(messages, {
 mt5_selection_required:'ยังไม่ได้เลือก MT5 สำหรับหน้าดาว',
 broker_clock_waiting_for_ticks:'บันทึก MT5 แล้ว รอราคาใหม่เพื่อยืนยันเวลาโบรกเกอร์อัตโนมัติ',
 broker_clock_unverified:'ยังยืนยันเวลาโบรกเกอร์ไม่ได้ ระบบจะตรวจใหม่เมื่อมีราคาใหม่',
 broker_disconnected:'MT5 ยังไม่เชื่อมเซิร์ฟเวอร์โบรกเกอร์',
 selected_terminal_not_running:messages.terminal_not_running,
 mt5_python_dependency_unavailable:'ยังขาดส่วนเชื่อม MT5 ในชุดติดตั้ง กรุณาใช้การซ่อมแซมการติดตั้ง HQ',
 mt5_discovery_expired:messages.discovery_expired,
 mt5_candidate_unavailable:messages.candidate_unavailable,
 mt5_candidate_changed:'รายการ MT5 เปลี่ยนแล้ว กรุณาค้นหาใหม่',
 selected_terminal_ambiguous:'มี MT5 จากตำแหน่งเดียวกันมากกว่าหนึ่งตัว จึงยังเลือกอัตโนมัติไม่ได้',
 selected_terminal_binding_mismatch:'โฟลเดอร์ข้อมูลไม่ตรงกับ MT5 ที่เปิดอยู่ กรุณาเลือกโปรไฟล์อื่น',
 terminal_data_path_unavailable:'ไม่พบโฟลเดอร์ข้อมูลของ MT5 นี้'
});
const timeThai = value => {
 const date = new Date(value);
 return value && Number.isFinite(date.getTime()) ? new Intl.DateTimeFormat('th-TH',{timeZone:'Asia/Bangkok',dateStyle:'short',timeStyle:'short'}).format(date) + ' น. ไทย' : 'ยังไม่มี';
};
async function jsonFetch(url, options = {}) {
 const response = await fetch(url, {...options, cache:'no-store', signal:AbortSignal.timeout(12000)});
 const data = await response.json();
 if (!response.ok) throw new Error(data.error || 'request_failed');
 return data;
}
const statusMessage = (value, fallback = 'รอตรวจข้อมูล') => messages[value] || fallback;
async function poll() {
 if (polling || saving || choosing) return;
 polling = true;
 try {
  const [setup, market] = await Promise.all([jsonFetch('/api/setup'), jsonFetch('/api/market')]);
  if (firstSetup) { $('#account-details').open = !setup.encryptedCredentialsPresent; firstSetup = false; }
  const s = market.sentiment || {}, c = market.correlations || {}, n = market.news || {}, mt = setup.mt5 || {};
  const available = s.items?.filter(item => item.available).length || 0;
  $('#status').textContent = statusMessage(s.status) + (available ? ` · ${available} สินทรัพย์` : '') + (setup.encryptedCredentialsPresent ? '\nมีบัญชีที่เก็บเข้ารหัสแล้ว' : '');
  $('#status').dataset.state = available ? 'ready' : 'error';
  const state = mt.reasonCode || mt.state || mt.status || c.errorCode || c.status;
  $('#mt5-status').textContent = (mt.selected?.label ? mt.selected.label + '\n' : '') + statusMessage(state, statusMessage(c.status)) + (c.coverage?.available ? `\nข้อมูลราคา ${c.coverage.available}/${c.coverage.total} สินทรัพย์` : '');
  $('#mt5-status').dataset.state = c.coverage?.available ? 'ready' : 'error';
  $('#sentiment-schedule').textContent = `ทุก 20 นาที · สำเร็จล่าสุด ${timeThai(s.lastSuccessAt)}\nตรวจครั้งถัดไป ${timeThai(s.nextAttemptAt)}`;
  $('#correlation-schedule').textContent = `ตรวจทุก 5 นาที · อ่านแท่ง H1 และคำนวณใหม่ตามรอบชั่วโมง\nสำเร็จล่าสุด ${timeThai(c.lastSuccessAt)}`;
  $('#news-status').textContent = `รายวัน เวลาไทย · ${statusMessage(n.status)}\nข่าววันนี้ ${n.events?.length || 0} รายการ · ${n.coverage?.thaiDayFullyCovered ? 'ปฏิทินครอบคลุมวันไทยนี้' : 'ยังตรวจความครบของวันนี้ไม่ได้'}\nสำเร็จล่าสุด ${timeThai(n.lastSuccessAt)}${n.nextAttemptAt ? '\nตรวจครั้งถัดไป ' + timeThai(n.nextAttemptAt) : ''}`;
  $('#service-status').textContent = setup.publicMirror === 'error' ? 'บริการข้อมูลทำงาน แต่ส่งข้อมูลเข้า HQ ไม่สำเร็จ กรุณาตรวจสิทธิ์โฟลเดอร์ติดตั้ง' : 'บริการบนเครื่องทำงาน · หน้าดาวจะรับข้อมูลใหม่อัตโนมัติ';
 } catch { $('#service-status').textContent = 'ติดต่อบริการบนเครื่องไม่สำเร็จ ระบบจะลองตรวจใหม่อัตโนมัติ'; }
 finally { polling = false; }
}
async function discover() {
 $('#discover').disabled = true; $('#select-mt5').disabled = true; $('#terminals').replaceChildren();
 $('#mt5-feedback').textContent = 'กำลังค้นหา MT5 ที่เปิดอยู่…';
 try {
  const data = await jsonFetch('/api/setup/mt5/candidates'); discoveryRevision = data.discoveryRevision;
  for (const candidate of data.candidates || []) {
   const label = document.createElement('label'); label.className = 'terminal-option';
   const input = document.createElement('input'); input.type = 'radio'; input.name = 'terminal'; input.value = candidate.candidateId; input.disabled = !candidate.selectable; input.required = true;
   input.addEventListener('change', () => { $('#select-mt5').disabled = !input.checked; });
   const text = document.createElement('span'); text.textContent = candidate.label || 'MetaTrader 5';
   const detail = document.createElement('small'); detail.textContent = candidate.selectable ? 'เปิดอยู่ · พร้อมให้เลือก' : statusMessage(candidate.reasonCode, 'ยังไม่พร้อมให้เลือก');
   text.append(detail); label.append(input, text); $('#terminals').append(label);
  }
  $('#mt5-feedback').textContent = data.candidates?.length ? 'เลือก MT5 ที่ต้องการใช้สำหรับข้อมูลหน้าดาว' : 'ยังไม่พบ MT5 ที่เปิดอยู่ เปิด MT5 แล้วกดค้นหาใหม่';
 } catch { $('#mt5-feedback').textContent = 'ค้นหา MT5 ไม่สำเร็จ กรุณาลองค้นหาใหม่'; }
 finally { $('#discover').disabled = false; }
}
async function post(url, body) {
 const setup = await jsonFetch('/api/setup');
 return jsonFetch(url, {method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':setup.csrf},body:JSON.stringify(body)});
}
$('#connect-form').addEventListener('submit', async event => {
 event.preventDefault(); $('#save').disabled = true; saving = true; $('#status').textContent = 'กำลังบันทึกแบบเข้ารหัส…';
 try {
  const data = await post('/api/setup/myfxbook', {email:$('#email').value,password:$('#password').value});
  $('#status').textContent = data.message; $('#account-details').open = false;
 } catch { $('#status').textContent = 'บันทึกไม่สำเร็จ กรุณาตรวจข้อมูลแล้วลองใหม่'; }
 finally { $('#password').value = ''; $('#save').disabled = false; saving = false; }
});
$('#mt5-form').addEventListener('submit', async event => {
 event.preventDefault(); const input = document.querySelector('input[name=terminal]:checked'); if (!input) return;
 choosing = true; $('#select-mt5').disabled = true; $('#mt5-feedback').textContent = 'กำลังบันทึก MT5 ของหน้าดาว…';
 try {
  const data = await post('/api/setup/mt5/select', {candidateId:input.value,discoveryRevision}); $('#mt5-feedback').textContent = data.message;
 } catch (error) { $('#mt5-feedback').textContent = statusMessage(error.message, 'ยังบันทึกไม่ได้ กรุณาค้นหา MT5 ใหม่'); }
 finally { choosing = false; $('#select-mt5').disabled = false; poll(); }
});
$('#discover').addEventListener('click', discover);
poll(); discover(); setInterval(poll, 5000);
