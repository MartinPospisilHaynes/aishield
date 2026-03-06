#!/usr/bin/env python3
import sys

with open("page.tsx", "r") as f:
    content = f.read()

old_span = '                                {q.risk_hint && q.risk_hint !== "none" && (\n                                    <span className="text-xs text-amber-300/80">\u26a0\ufe0f {q.risk_hint}</span>\n                                )}'
count1 = content.count(old_span)
content = content.replace(old_span, "")

old_cond = '((q.risk_hint && q.risk_hint !== "none") || q.ai_act_article)'
count2 = content.count(old_cond)
content = content.replace(old_cond, "q.ai_act_article")

old_comment = "{/* Risk hint + AI Act article \u2014 pod textem ot\u00e1zky */}"
count3 = content.count(old_comment)
content = content.replace(old_comment, "{/* AI Act article \u2014 pod textem ot\u00e1zky */}")

with open("page.tsx", "w") as f:
    f.write(content)

print(f"span={count1} cond={count2} comment={count3}")
