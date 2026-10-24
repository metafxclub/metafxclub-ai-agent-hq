// Educational summaries checked against the primary sources linked below.
// These explain definitions; they do not fetch news, fill missing actual values,
// or turn the fictional calendar into a live forecast. Reviewed 2026-10-24.
const EXPLAINERS = {
  pmi: {
    title: 'PMI · ดัชนีผู้จัดการฝ่ายจัดซื้อ',
    lines: [
      'สำรวจภาวะธุรกิจ เป็นค่าดัชนี ไม่ใช่ % การเติบโต',
      '50 = คงเดิม; สูงกว่า = ขยาย; ต่ำกว่า = หดจากเดือนก่อน',
      'ดีขึ้นแต่ยังต่ำกว่า 50 = ยังหดตัว; เทียบค่าคาดด้วย',
      'ค่าเงินอาจตอบสนองผ่านมุมมองเศรษฐกิจและดอกเบี้ย',
    ],
    sourceName: 'S&P Global · PMI FAQ',
    sourceUrl: 'https://www.spglobal.com/market-intelligence/en/solutions/products/resources/pmi-faq',
  },
  consumerConfidence: {
    title: 'ความเชื่อมั่นผู้บริโภค',
    lines: [
      'สำรวจมุมมองต่อการเงิน เศรษฐกิจ และการใช้จ่าย',
      'เป็นดุลคำตอบเชิงบวก–ลบ ไม่ใช่อัตราโตของยอดขาย',
      'สูงขึ้นคือมุมมองดีขึ้น; เทียบคาดการณ์และครั้งก่อน',
      'อาจหนุนมุมมองเศรษฐกิจ แต่ไม่ยืนยันทิศค่าเงิน',
    ],
    sourceName: 'European Commission · วิธีอ่านแบบสำรวจ',
    sourceUrl: 'https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/methodology-business-and-consumer-surveys/methodological-concepts_en',
  },
  businessConfidence: {
    title: 'ANZ · ความเชื่อมั่นธุรกิจ',
    lines: [
      'สำรวจมุมมองธุรกิจนิวซีแลนด์ต่อเศรษฐกิจข้างหน้า',
      'ดุลสุทธิคือฝั่งมองดีหักฝั่งมองแย่ ไม่ใช่ GDP',
      'แยกความมั่นใจรวมจากแนวโน้มกิจการของผู้ตอบ',
      'เทียบคาดและครั้งก่อน; ค่าเงินยังขึ้นกับปัจจัยอื่น',
    ],
    sourceName: 'ANZ · Business Outlook',
    sourceUrl: 'https://www.anz.co.nz/about-us/economic-markets-research/business-outlook/',
  },
  cpi: {
    title: 'CPI · เงินเฟ้อผู้บริโภค',
    lines: [
      'วัดการเปลี่ยนราคาสินค้าและบริการของผู้บริโภค',
      'm/m เทียบเดือนก่อน; y/y เทียบเดือนเดียวกันปีก่อน',
      'เงินเฟ้อลดลง อาจแค่ราคาเพิ่มช้าลง ไม่ใช่ราคาลด',
      'เกินคาดอาจดันมุมมองดอกเบี้ยขึ้น ค่าเงินไม่แน่นอน',
    ],
    sourceName: 'BLS · CPI FAQ',
    sourceUrl: 'https://www.bls.gov/cpi/questions-and-answers.htm',
  },
  coreCpi: {
    title: 'Core CPI · เงินเฟ้อพื้นฐานสหรัฐฯ',
    lines: [
      'CPI สหรัฐฯ ที่ไม่นับอาหารและพลังงาน',
      'ช่วยดูแรงกดดันราคาพื้นฐาน โดยยังต้องอ่าน CPI รวม',
      'เทียบคาดและครั้งก่อนในช่วงเวลาเดียวกัน เช่น m/m',
      'เกินคาดอาจหนุนดอกเบี้ยสูงนาน แต่ไม่ยืนยันทิศกราฟ',
    ],
    sourceName: 'BLS · Headline และ Core CPI',
    sourceUrl: 'https://www.bls.gov/cpi/factsheets/common-misconceptions-about-cpi.htm',
  },
  canadaCpi: {
    title: 'CPI · เงินเฟ้อแคนาดา',
    lines: [
      'วัดการเปลี่ยนราคาตะกร้าสินค้าและบริการผู้บริโภค',
      'm/m เทียบเดือนก่อน; y/y เทียบเดือนเดียวกันปีก่อน',
      'อ่านผลเทียบคาด ไม่สรุปจากตัวเลขสูงขึ้นอย่างเดียว',
      'CAD อาจตอบสนองผ่านมุมมองดอกเบี้ยและปัจจัยอื่น',
    ],
    sourceName: 'Statistics Canada · CPI FAQ',
    sourceUrl: 'https://www.statcan.gc.ca/en/subjects-start/prices_and_price_indexes/consumer_price_indexes/faq',
  },
  japanCpi: {
    title: 'CPI · เงินเฟ้อญี่ปุ่นรายปี',
    lines: [
      'วัดการเปลี่ยนราคาสินค้าและบริการที่ครัวเรือนซื้อ',
      'รายปีเทียบเดือนเดียวกันปีก่อน ไม่ใช่เดือนก่อน',
      'เทียบคาดการณ์ และแยกเงินเฟ้อรวมจากดัชนีพื้นฐาน',
      'JPY อาจตอบสนองผ่านมุมมอง BOJ ไม่ใช่ตัวเลขเดียว',
    ],
    sourceName: 'Statistics Bureau Japan · CPI Q&A',
    sourceUrl: 'https://www.stat.go.jp/english/data/cpi/1585.htm',
  },
  unemployment: {
    title: 'อัตราว่างงาน',
    lines: [
      'ผู้ว่างงานหารกำลังแรงงาน ไม่ใช่ประชากรทั้งหมด',
      'สูงขึ้นอาจสะท้อนแรงงานอ่อนลง ไม่ใช่ข่าวดีเสมอ',
      'เทียบคาด พร้อมดูค่าจ้างและการมีส่วนร่วมแรงงาน',
      'ค่าเงินอาจอ่อนหากตลาดคาดลดดอกเบี้ย แต่ไม่เสมอ',
    ],
    sourceName: 'ONS · คู่มือสถิติตลาดแรงงาน',
    sourceUrl: 'https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/aguidetolabourmarketstatistics/',
  },
  employment: {
    title: 'การเปลี่ยนแปลงการจ้างงาน',
    lines: [
      'จำนวนผู้มีงานทำที่เปลี่ยนจากเดือนก่อน',
      'ครอบคลุมงานเต็มเวลาและพาร์ตไทม์ ไม่ใช่ค่าจ้าง',
      'เทียบคาด พร้อมดูชั่วโมงทำงานและอัตราว่างงาน',
      'เกินคาดอาจหนุน AUD หากมุมมองเศรษฐกิจดีขึ้น',
    ],
    sourceName: 'ABS · Labour force framework',
    sourceUrl: 'https://www.abs.gov.au/statistics/detailed-methodology-information/concepts-sources-methods/labour-statistics-concepts-sources-and-methods/2023/concepts-and-sources/labour-force-framework',
  },
  ecbSpeech: {
    title: 'ถ้อยแถลง ECB',
    lines: [
      'ติดตามมุมมองเงินเฟ้อและแนวทางดอกเบี้ยของ ECB',
      'เข้มขึ้นเน้นคุมเงินเฟ้อ; ผ่อนคลายเน้นหนุนเศรษฐกิจ',
      'ดูว่าต่างจากตลาดคาดอย่างไร ไม่มีค่าคาดแบบตัวเลข',
      'อาจเปลี่ยนมุมมองต่อ EUR แต่ยังไม่ใช่มติขึ้นดอกเบี้ย',
    ],
    sourceName: 'ECB · นโยบายการเงินคืออะไร',
    sourceUrl: 'https://www.ecb.europa.eu/ecb-and-you/explainers/tell-me/html/what-is-monetary-policy.en.html',
  },
  fedSpeech: {
    title: 'ถ้อยแถลง Fed',
    lines: [
      'ติดตามมุมมองเศรษฐกิจ เงินเฟ้อ และดอกเบี้ยสหรัฐฯ',
      'เข้มขึ้นอาจชี้ดอกเบี้ยสูงนาน; ผ่อนคลายอาจตรงข้าม',
      'ดูสิ่งที่ต่างจากตลาดคาด ไม่ใช่ทุกคำพูดคือมติ Fed',
      'USD อาจขยับผ่านคาดการณ์ดอกเบี้ยและปัจจัยอื่น',
    ],
    sourceName: 'Federal Reserve · ดอกเบี้ยคาดการณ์กับค่าเงิน',
    sourceUrl: 'https://www.federalreserve.gov/econres/notes/ifdp-notes/the-sensitivity-of-the-us-dollar-exchange-rate-to-changes-in-monetary-policy-expectations-20170922.htm',
  },
  snbSpeech: {
    title: 'ถ้อยแถลง SNB',
    lines: [
      'ติดตามนโยบายเงินเฟ้อและดอกเบี้ยสวิตเซอร์แลนด์',
      'มองหาท่าทีที่เปลี่ยนจากเดิมและจากตลาดคาด',
      'ไม่มีผลตัวเลขเทียบคาด และไม่ใช่มตินโยบายเสมอไป',
      'CHF อาจตอบสนอง แต่ยังขึ้นกับเศรษฐกิจและความเสี่ยง',
    ],
    sourceName: 'SNB · นโยบายการเงิน',
    sourceUrl: 'https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy',
  },
  generic: {
    title: 'อ่านข่าวเศรษฐกิจอย่างไร',
    lines: [
      'เริ่มจากชื่อ หน่วย และช่วงเวลาที่ตัวเลขครอบคลุม',
      'แยกการเทียบคาดการณ์ออกจากการเทียบครั้งก่อน',
      'ยังไม่มีผลจริง ให้อ่านเพียงฉากทัศน์ตามเงื่อนไข',
      'ข่าวเดียวไม่ยืนยันทิศกราฟหรือแนวโน้มระยะยาว',
    ],
    sourceName: 'Federal Reserve · ความคาดหวังกับค่าเงิน',
    sourceUrl: 'https://www.federalreserve.gov/econres/notes/ifdp-notes/the-sensitivity-of-the-us-dollar-exchange-rate-to-changes-in-monetary-policy-expectations-20170922.htm',
  },
};

function categoryFor(event) {
  if (!event || typeof event !== 'object') return 'generic';
  const title = typeof event.title === 'string' ? event.title : '';
  if (/\bPMI\b/i.test(title)) return 'pmi';
  if (event.metric === 'inflation') {
    if (event.currency === 'JPY') return 'japanCpi';
    if (event.currency === 'CAD') return 'canadaCpi';
    if (event.currency === 'USD') return /\bcore\b/i.test(title) ? 'coreCpi' : 'cpi';
  }
  if (event.metric === 'confidence') {
    if (event.currency === 'EUR') return 'consumerConfidence';
    if (event.currency === 'NZD') return 'businessConfidence';
  }
  if (event.metric === 'unemployment') return 'unemployment';
  if (event.metric === 'employment' && event.currency === 'AUD') return 'employment';
  if (event.kind === 'speech') {
    if (event.currency === 'EUR') return 'ecbSpeech';
    if (event.currency === 'USD') return 'fedSpeech';
    if (event.currency === 'CHF') return 'snbSpeech';
  }
  return 'generic';
}

export function getNewsExplainer(event) {
  const explainer = EXPLAINERS[categoryFor(event)];
  // Return a fresh list so one expanded panel cannot mutate another event.
  return { ...explainer, lines: [...explainer.lines] };
}
