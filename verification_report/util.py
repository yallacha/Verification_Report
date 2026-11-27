"""경로 정규화와 모듈 판정 등 공용 함수."""
from __future__ import annotations

import re
from typing import Iterable, Tuple

DEFAULT_ROOTS: Tuple[str, ...] = ("src", "include", "tests")
_ABS = re.compile(r"^(/|[A-Za-z]:)")


def norm_path(path: str, roots: Iterable[str] = DEFAULT_ROOTS, strip: Iterable[str] = ()) -> str:
    """도구마다 다른 경로 표기(절대/상대, 역슬래시)를 저장소 기준 상대 경로로 맞춘다."""
    p = path.replace("\\", "/")
    for prefix in strip:
        prefix = prefix.replace("\\", "/")
        if p.startswith(prefix):
            p = p[len(prefix):]
    while p.startswith("./"):
        p = p[2:]
    parts = [x for x in p.split("/") if x and x != "."]
    if _ABS.match(p):
        for i, part in enumerate(parts):
            if part in roots:
                return "/".join(parts[i:])
    return "/".join(parts)


def module_of(path: str, roots: Iterable[str] = DEFAULT_ROOTS) -> str:
    """모듈 = src/ 아래 첫 하위 디렉터리. 파일이 바로 src/ 에 있으면 파일 이름(확장자 제외).

    C 에서는 .c/.h 쌍이 하나의 모듈이므로 `src/foo.c` 와 `include/foo.h` 는 모듈 `foo` 이다.
    """
    parts = [x for x in path.split("/") if x]
    if not parts:
        return "(unknown)"
    if parts[0] in roots and len(parts) > 1:
        parts = parts[1:]
    if len(parts) > 1:
        return parts[0]
    stem = parts[0].rsplit(".", 1)[0]
    return stem or parts[0]


def fmt_pct(value: float) -> str:
    return f"{value:.2f}%"


def fmt_num(value: float) -> str:
    return f"{value:,.0f}"
