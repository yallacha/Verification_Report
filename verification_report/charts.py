"""의존성 없는 인라인 SVG 차트. 색은 CSS 클래스(테마 변수)로 지정해 다크 모드에서도 동작한다."""
from __future__ import annotations

import math
from html import escape as h
from typing import List, Optional, Sequence, Tuple


def donut(segments: Sequence[Tuple[str, float, str]], center: str, sub: str = "") -> str:
    """segments: (라벨, 값, CSS 클래스 접미사)."""
    r, cx, cy = 58, 80, 80
    circ = 2 * math.pi * r
    total = sum(v for _, v, _ in segments)
    label = ", ".join(f"{l} {v:g}" for l, v, _ in segments)
    parts = [f'<svg class="chart" viewBox="0 0 160 160" role="img" aria-label="{h(label)}">',
             f'<circle cx="{cx}" cy="{cy}" r="{r}" class="track" fill="none" stroke-width="22"/>']
    offset = 0.0
    if total > 0:
        for seg_label, value, cls in segments:
            if value <= 0:
                continue
            dash = circ * value / total
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke-width="22" class="seg-{cls}" '
                f'stroke-dasharray="{dash:.2f} {circ - dash:.2f}" stroke-dashoffset="{-offset:.2f}" '
                f'transform="rotate(-90 {cx} {cy})"><title>{h(seg_label)}: {value:g}</title></circle>')
            offset += dash
    parts.append(f'<text x="{cx}" y="{cy + 2}" text-anchor="middle" class="big">{h(center)}</text>')
    if sub:
        parts.append(f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" class="small">{h(sub)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def hbars(items: Sequence[Tuple[str, float, str, Optional[float]]], width: int = 520) -> str:
    """가로 막대(0~100%). items: (라벨, 퍼센트, 값 문자열, 기준 퍼센트|None). 기준 미달은 빨강."""
    if not items:
        return '<p class="empty">표시할 데이터가 없습니다.</p>'
    label_w, value_w, row_h = 150, 112, 30
    bar_w = width - label_w - value_w
    height = row_h * len(items) + 6
    parts = [f'<svg class="chart wide" viewBox="0 0 {width} {height}" role="img" aria-label="커버리지 막대 차트">']
    for i, (label, pct, text, gate) in enumerate(items):
        y = i * row_h + 4
        pct = max(0.0, min(100.0, pct))
        cls = "info" if gate is None else ("pass" if pct >= gate else "fail")
        parts.append(f'<text x="0" y="{y + 15}" class="lbl">{h(label)}</text>')
        parts.append(f'<rect x="{label_w}" y="{y + 3}" width="{bar_w}" height="14" rx="3" class="track-fill"/>')
        if pct > 0:
            parts.append(f'<rect x="{label_w}" y="{y + 3}" width="{bar_w * pct / 100:.1f}" height="14" rx="3" '
                         f'class="fill-{cls}"><title>{h(label)} {pct:.2f}%</title></rect>')
        if gate is not None:
            gx = label_w + bar_w * gate / 100
            parts.append(f'<line x1="{gx:.1f}" x2="{gx:.1f}" y1="{y}" y2="{y + 20}" class="gate-line"/>')
        parts.append(f'<text x="{label_w + bar_w + 8}" y="{y + 15}" class="val">{h(text)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def vbars(items: Sequence[Tuple[str, float, str]], width: int = 460, height: int = 170) -> str:
    """세로 막대. items: (x 라벨, 값, CSS 클래스 접미사)."""
    if not items or all(v == 0 for _, v, _ in items):
        return '<p class="empty">표시할 데이터가 없습니다.</p>'
    top, bottom, left = 18, 30, 8
    plot_h, plot_w = height - top - bottom, width - left * 2
    vmax = max(v for _, v, _ in items)
    slot = plot_w / len(items)
    bw = min(46.0, slot * 0.62)
    parts = [f'<svg class="chart wide" viewBox="0 0 {width} {height}" role="img" aria-label="막대 차트">',
             f'<line x1="{left}" x2="{width - left}" y1="{top + plot_h}" y2="{top + plot_h}" class="axis"/>']
    for i, (label, value, cls) in enumerate(items):
        x = left + slot * i + (slot - bw) / 2
        bh = plot_h * value / vmax if vmax else 0
        y = top + plot_h - bh
        if value > 0:
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" class="fill-{cls}">'
                         f'<title>{h(label)}: {value:g}</title></rect>')
        parts.append(f'<text x="{x + bw / 2:.1f}" y="{y - 4:.1f}" text-anchor="middle" class="val">{value:g}</text>')
        parts.append(f'<text x="{x + bw / 2:.1f}" y="{height - 10}" text-anchor="middle" class="lbl">{h(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)
