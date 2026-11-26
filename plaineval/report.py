# -*- coding: utf-8 -*-
"""生成单文件 HTML 报告（无外部依赖，可离线打开 / Ctrl+P 导出 PDF）"""
from __future__ import annotations

import html

CSS = """
:root{--bg:#fdfcf8;--ink:#1c1b19;--ink2:#3d3a35;--muted:#6f6a62;--rule:#e3ded3;
 --rule2:#efeae0;--accent:#8b4513;--accent-soft:#f4ebdf;--key:#1f5f4e;--key-bg:#eaf3ef;
 --warn:#8a5a00;--warn-bg:#fdf4e3;--bad:#8c2f2f;--bad-bg:#fbeeee;
 --mono:ui-monospace,Menlo,Consolas,monospace;
 --serif:"Songti SC","Source Han Serif SC","Noto Serif SC",Georgia,serif;
 --sans:"PingFang SC","Source Han Sans SC",-apple-system,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--serif);font-size:16px;line-height:1.8}
main{max-width:900px;margin:0 auto;padding:48px 32px 100px}
.kicker{font-family:var(--sans);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin-bottom:10px}
h1{font-size:1.8em;margin:0 0 12px;font-weight:600;line-height:1.3}
h2{font-size:1.2em;margin:44px 0 14px;padding-top:18px;border-top:1px solid var(--rule);font-weight:600}
h3{font-size:1em;margin:24px 0 8px;font-weight:600}
p{margin:0 0 12px;color:var(--ink2)}ul{margin:0 0 14px;padding-left:1.3em}li{margin:0 0 5px}
code{font-family:var(--mono);font-size:.85em;background:#f4f1ea;padding:1px 5px;border-radius:3px;color:#5a3a1e}
table{width:100%;border-collapse:collapse;margin:14px 0 20px;font-size:.85em;font-family:var(--sans)}
th{text-align:left;font-weight:600;font-size:11.5px;color:var(--muted);border-bottom:1.5px solid var(--rule);padding:7px 8px 7px 0}
td{padding:6px 8px 6px 0;border-bottom:1px solid var(--rule2);vertical-align:top}
td:first-child{font-weight:500}
.num{font-family:var(--mono);font-size:.92em}
.dim{color:var(--muted)}
.box{border-left:3px solid var(--accent);padding:13px 17px;margin:16px 0;background:#fff}
.box.key{border-left-color:var(--key);background:var(--key-bg)}
.box.warn{border-left-color:var(--warn);background:var(--warn-bg)}
.box.bad{border-left-color:var(--bad);background:var(--bad-bg)}
.box .l{font-family:var(--sans);font-size:10.5px;letter-spacing:.15em;text-transform:uppercase;display:block;margin-bottom:6px;font-weight:600;color:var(--accent)}
.box.key .l{color:var(--key)}.box.warn .l{color:var(--warn)}.box.bad .l{color:var(--bad)}
.badge{display:inline-block;font-family:var(--sans);font-size:10.5px;border-radius:3px;padding:0 6px;font-weight:600}
.b-base{background:var(--key-bg);color:var(--key);border:1px solid #bcd9ce}
.b-eval{background:var(--warn-bg);color:var(--warn);border:1px solid #e8d3a3}
.b-hold{background:#eee9df;color:var(--muted);border:1px solid var(--rule)}
footer{margin-top:56px;padding-top:18px;border-top:1px solid var(--rule);font-family:var(--sans);font-size:11.5px;color:var(--muted)}
@media print{body{font-size:9.5pt}main{padding:0}h2{page-break-after:avoid}table,.box{page-break-inside:avoid}}
"""


def e(x):
    return html.escape(str(x))


def _badge(role):
    cls = "b-base" if "基线" in role else "b-eval" if "评估" in role else "b-hold"
    return f'<span class="badge {cls}">{e(role)}</span>'


def _fmt(v):
    return "—" if v is None else (f"{v:g}" if isinstance(v, float) else str(v))


def write_html(res: dict, path: str) -> None:
    meta = res.get("case", {})
    A, B = res["A"], res["B"]
    an = meta.get("a_name", "A")
    bn = meta.get("b_name", "B")

    p = []
    p.append(f"""<div class="kicker">信息组织评测报告 · plain-language-eval</div>
<h1>{e(meta.get('case_id', 'Case'))}　信息组织八项结果</h1>
<p class="dim">A = {e(an)}　B = {e(bn)}
{f'　人工偏好：{e(meta.get("human_preference"))}' if meta.get("human_preference") else ''}</p>""")

    # 总表
    p.append("<h2>一、对照总表</h2>")
    rows = "".join(
        f"<tr><td>{e(r['指标'])}</td><td class='num'>{_fmt(r['A'])}</td>"
        f"<td class='num'>{_fmt(r['B'])}</td></tr>" for r in res["compare"])
    p.append(f"<table><thead><tr><th>指标</th><th>{e(an)}</th><th>{e(bn)}</th></tr></thead>"
             f"<tbody>{rows}</tbody></table>")

    # 归属
    p.append("<h2>二、八项归属</h2>")
    rows = "".join(f"<tr><td>{e(k)}</td><td>{_badge(v)}</td></tr>"
                   for k, v in A["ROLE"].items())
    p.append(f"<table><thead><tr><th>对象</th><th>归属</th></tr></thead><tbody>{rows}</tbody></table>")
    p.append("""<div class="box key"><span class="l">怎么读这份报告</span>
<p><strong>基线</strong>只报数、不判优劣——句长、块数、集中度都没有绝对好坏，阈值等样本积累后再划。</p>
<p><strong>评估</strong>抓明确的错。只有达到「换个人看也一样」的判据才能扣分。</p>
<p><strong>B6 是观察项</strong>：四种口径给出三个方向，暂不计分。</p></div>""")

    # A1 / A2 / A3
    p.append("<h2>三、措辞层：A1 / A2 / A3</h2>")
    for name, r in ((an, A), (bn, B)):
        a1, a2, a3 = r["A1_词汇多样性"], r["A2_用词熟悉度"], r["A3_句法"]
        p.append(f"<h3>{e(name)}</h3>")
        p.append("<table><tbody>"
                 f"<tr><td>A1 词次 / 词型</td><td class='num'>{a1['N_词次']} / {a1['V_词型']}</td></tr>"
                 f"<tr><td>A1 MSTTR-50</td><td class='num'>{_fmt(a1['MSTTR50'])}</td></tr>"
                 f"<tr><td>A1 尾部丢弃词数</td><td class='num'>{a1['尾部丢弃词数']}</td></tr>"
                 f"<tr><td>A2 候选词数</td><td class='num'>{a2['候选词数']}</td></tr>"
                 f"<tr><td>A2 判过 / 豁免 / 未解释</td><td class='num'>"
                 f"{_fmt(a2.get('判过概念数'))} / {_fmt(a2.get('豁免数'))} / "
                 f"<strong>{_fmt(a2.get('未解释陌生概念数'))}</strong></td></tr>"
                 f"<tr><td>A3 句长均值 / P90</td><td class='num'>{_fmt(a3['句长均值'])} / {_fmt(a3['句长P90'])}</td></tr>"
                 f"<tr><td>A3 T-unit 数</td><td class='num'>{a3['T-unit数']}</td></tr>"
                 f"<tr><td>A3 每 T-unit 从句数</td><td class='num'>{_fmt(a3['每T-unit从句数'])}</td></tr>"
                 "</tbody></table>")
        if a2.get("未解释清单"):
            p.append(f"<p class='dim'>A2 未解释：{'、'.join(e(x) for x in a2['未解释清单'])}</p>")
    p.append("""<div class="box warn"><span class="l">A1 / A3 权重为 0</span>
<p>A1 的词频熵与篇幅 ρ≈0.95，本质是篇幅替身；MSTTR 与人工偏好只有 4/7 一致。</p>
<p>A3 句长是提示不是判据——长句不等于难读。两者只作基线。</p></div>""")
    p.append("""<div class="box key"><span class="l">A2 是唯一计分项，但 K 值 pending</span>
<p>本轮只报计数（判过 / 豁免 / 未解释），不产出分数。未解释概念该扣多少分取决于读者群体，
没有跨 case 数据定 K 就是拍脑袋。</p></div>""")

    # B1
    p.append("<h2>四、B1 覆盖</h2>")
    for name, r in ((an, A), (bn, B)):
        c = r["B1_覆盖"]
        p.append(f"<h3>{e(name)}</h3><p>诉求 {c['total']} 项：覆盖 {c['covered']}，"
                 f"部分 {len(c['partial'])}，缺口 {len(c['missing'])}</p>")
        if c["missing"]:
            p.append(f"<p class='dim'>缺：{'、'.join(e(x) for x in c['missing'])}</p>")

    # B2
    p.append("<h2>五、B2 诉求位置</h2>")
    rows = ""
    for x, y in zip(A["B2_在哪"]["诉求位置"], B["B2_在哪"]["诉求位置"]):
        pa = "漏答" if x["position_pct"] is None else f"{x['position_pct']}%"
        pb = "漏答" if y["position_pct"] is None else f"{y['position_pct']}%"
        rows += (f"<tr><td>{e(x['label'])}</td><td class='num'>{pa}</td>"
                 f"<td class='num'>{pb}</td><td class='dim'>{e(x['block_title'])}</td></tr>")
    p.append(f"<table><thead><tr><th>诉求</th><th>{e(an)}</th><th>{e(bn)}</th>"
             f"<th>{e(an)} 落点</th></tr></thead><tbody>{rows}</tbody></table>")

    # B3
    p.append("<h2>六、B3 散不散</h2>")
    for name, r in ((an, A), (bn, B)):
        m = r["B3_散不散"]["微观"]
        g = r["B3_散不散"]["宏观"]
        p.append(f"<h3>{e(name)}</h3>")
        p.append("<table><tbody>"
                 f"<tr><td>延续率</td><td class='num'>{_fmt(m['延续率_CONTINUE'])}</td></tr>"
                 f"<tr><td>切换率</td><td class='num'>{_fmt(m['切换率_SHIFT'])}</td></tr>"
                 f"<tr><td>指称距离</td><td class='num'>{_fmt(m['指称距离_平均间隔句'])} 句</td></tr>"
                 f"<tr><td>平均集中度</td><td class='num'>{_fmt(g['平均集中度'])}</td></tr>"
                 f"<tr><td>平均跨度</td><td class='num'>{_fmt(g['平均跨度pct'])}%</td></tr>"
                 "</tbody></table>")
        dist = m["共享强度占比pct"]
        p.append("<p class='dim'>共享强度分布：" +
                 "　".join(f"{e(k)} {v}%" for k, v in dist.items()) + "</p>")

    p.append("""<div class="box warn"><span class="l">必须看分布</span>
<p>词面重叠（连续值）和实体延续率（二元值）可能给出相反方向。均值会把「两极分化」和「均匀型」抹成同一个数。</p></div>""")

    # B4
    p.append("<h2>七、B4 层级</h2>")
    keys = ["标题块数", "块字数中位数", "Markdown标题数", "标题层级深度",
            "列表项数", "列表项平均字数", "列表项占比"]
    rows = "".join(f"<tr><td>{e(k)}</td><td class='num'>{_fmt(A['B4_层级'].get(k))}</td>"
                   f"<td class='num'>{_fmt(B['B4_层级'].get(k))}</td></tr>" for k in keys)
    p.append(f"<table><thead><tr><th>指标</th><th>{e(an)}</th><th>{e(bn)}</th></tr></thead>"
             f"<tbody>{rows}</tbody></table>")
    p.append("""<div class="box"><span class="l">最稳的一项</span>
<p><strong>列表项平均字数</strong>：它不依赖块识别，换格式也不会变。</p>
<p>45 字/条 = 一条里塞两三句话（段落伪装成列表）；19 字/条 = 一条一件事。</p></div>""")

    # B5
    p.append("<h2>八、B5 状态 vs 推理（需人工判档）</h2>")
    if res.get("A", {}).get("B5_状态vs推理", {}).get("QUD"):
        rows = "".join(f"<tr><td>{e(q['id'])}</td><td>{e(q['question'])}</td></tr>"
                       for q in A["B5_状态vs推理"]["QUD"])
        p.append(f"<table><thead><tr><th>QUD</th><th>预设问题</th></tr></thead><tbody>{rows}</tbody></table>")
    for name, r in ((an, A), (bn, B)):
        b = r["B5_状态vs推理"]
        p.append(f"<p><strong>{e(name)}</strong>：作者句 {b['作者句数']}，候选 {b['候选数']} 句</p>")
    p.append("""<div class="box warn"><span class="l">这一步机器做不了</span>
<p>脚本只把带「不能/不等于/尚未/以上是建议」的句子捞出来。<strong>初筛召回率高、精度低——候选里大部分是正常句，必须逐句判档。</strong></p>
<p>判档问法：这句回答的是哪个 QUD？如果答的是「状态」，关键状态给了吗？</p></div>""")

    # B7 / B8
    p.append("<h2>九、B7 指代 / B8 数量自述</h2>")
    rows = (f"<tr><td>B7 回指数</td><td class='num'>{A['B7_指代']['回指数']}</td>"
            f"<td class='num'>{B['B7_指代']['回指数']}</td></tr>"
            f"<tr><td>B7 需配对数</td><td class='num'>{A['B7_指代']['需配对数']}</td>"
            f"<td class='num'>{B['B7_指代']['需配对数']}</td></tr>"
            f"<tr><td>B8 声明不一致</td><td class='num'>{A['B8_数量自述']['声明不一致数']}</td>"
            f"<td class='num'>{B['B8_数量自述']['声明不一致数']}</td></tr>"
            f"<tr><td>B8 序数不一致</td><td class='num'>{A['B8_数量自述']['序数不一致数']}</td>"
            f"<td class='num'>{B['B8_数量自述']['序数不一致数']}</td></tr>")
    p.append(f"<table><thead><tr><th>指标</th><th>{e(an)}</th><th>{e(bn)}</th></tr></thead>"
             f"<tbody>{rows}</tbody></table>")
    p.append("""<div class="box"><span class="l">B7 的一档可扣分</span>
<p><strong>需读者自己配对</strong>：如「前一份 / 后一份」，要回前文数出两个对象才能对上。这不是「不清」，但读者要额外推理。</p></div>""")

    p.append("""<footer>
<p><strong>plain-language-eval</strong>　单文件 HTML，无外部依赖，可离线打开与 Ctrl+P 导出 PDF。</p>
<p>自动指标可用 <code>plaineval</code> 复算；判题部分（B5/B6/B7 分档）需人或 LLM 确认后写回 aspects.json。</p>
</footer>""")

    doc = (f"<!DOCTYPE html><html lang='zh-CN'><head><meta charset='UTF-8'>"
           f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
           f"<title>{e(meta.get('case_id', 'Case'))} 信息组织评测</title>"
           f"<style>{CSS}</style></head><body><main>{''.join(p)}</main></body></html>")
    open(path, "w", encoding="utf-8").write(doc)
