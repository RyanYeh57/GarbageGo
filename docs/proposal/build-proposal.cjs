// 合併提案章節、文獻摘要表與引用編號；原始章節保持不變。
const fs = require('fs');
const path = require('path');
const dir = __dirname;
const read = name => fs.readFileSync(path.join(dir, name), 'utf8').replace(/\r\n/g, '\n');
const files = ['01-abstract.md', '02-introduction.md', '03a-related-work-ai.md', '03b-related-work-domain.md', '03c-research-gap.md', '04-deep-research.md', '05-proposed-scheme.md'];
const texts = Object.fromEntries(files.map(name => [name, read(name)]));
const sourceFiles = ['02-introduction.md', '03a-related-work-ai.md', '03b-related-work-domain.md', '04-deep-research.md'];
const refs = new Map();
for (const name of sourceFiles) {
  const section = texts[name].split(/\n## (?:References|參考文獻)\n/)[1]?.split(/\n## /)[0] || '';
  for (const line of section.split('\n')) {
    const match = line.match(/^(?:- )?\[([IBCD]\d+)\]\s+(.+)$/);
    if (!match) continue;
    const url = match[2].match(/https?:\/\/[^\s<>\])）]+/)?.[0];
    if (!url) throw new Error(`參考文獻沒有 URL：${match[1]}`);
    refs.set(match[1], { text: match[2], url: url.replace(/[.,。]+$/, '') });
  }
}
const numbers = new Map();
const entries = [];
const replaceCitations = text => text.replace(/\[([IBCD]\d+)([^\]]*)\]/g, (whole, key, suffix) => {
  const ref = refs.get(key);
  if (!ref) throw new Error(`找不到引用：${key}`);
  if (!numbers.has(ref.url)) {
    numbers.set(ref.url, entries.length + 1);
    entries.push({ ...ref, aliases: [] });
  }
  const n = numbers.get(ref.url);
  if (!entries[n - 1].aliases.includes(key)) entries[n - 1].aliases.push(key);
  return `[${n}${suffix}]`;
});
const getTable = name => {
  const lines = texts[name].split('\n');
  const index = lines.findIndex(line => line.startsWith('| Ref. | Year |'));
  if (index < 0) throw new Error(`找不到摘要表：${name}`);
  const result = [];
  for (let i = index; i < lines.length && lines[i].startsWith('|'); i++) result.push(lines[i]);
  return result;
};
const a = getTable('03a-related-work-ai.md');
const b = getTable('03b-related-work-domain.md');
let combined = '# GarbageGo Proposal\n\n> 整合草稿：內容和設計仍待確認；未完成實驗的敘述均為規劃或預期結果。\n\n';
for (const name of files) {
  let body = texts[name].split(/\n## (?:References|參考文獻)\n/)[0];
  if (name === '03a-related-work-ai.md') {
    body = body.replace(/\n## 4\. Article Summary Table\n[\s\S]*$/, '');
  }
  if (name === '03b-related-work-domain.md') {
    body = body.replace(/\n## 1\. 文獻摘要表\n[\s\S]*?(?=\n## 2\.)/, '\n');
  }
  combined += replaceCitations(body.trim()) + '\n\n';
  if (name === '03b-related-work-domain.md') {
    combined += '## Article Summary Table：AI 與領域研究\n\n' + replaceCitations([...a, ...b.slice(2)].join('\n')) + '\n\n';
  }
}
const references = '# 6. References\n\n> 依整合草稿首次引用順序編號；括號內為原章節代號，供核對。資料與原文仍需逐篇複核。\n\n' + entries.map((entry, i) => `[${i + 1}] ${entry.text} （原代號：${entry.aliases.join('、')}）`).join('\n\n') + '\n';
fs.writeFileSync(path.join(dir, '06-references.md'), references, 'utf8');
fs.writeFileSync(path.join(dir, 'proposal-integrated.md'), combined + references, 'utf8');
console.log(`已整合 ${files.length} 個章節、${a.length + b.length - 4} 筆摘要及 ${entries.length} 筆去重參考資料。`);
