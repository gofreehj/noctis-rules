#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_noctis_rules.py
将 Loyalsoldier/clash-rules 和 Loyalsoldier/v2ray-rules-dat 移植为 Noctis 专属分流规则集。
参考 lyc8503/sing-box-rules 的自动构建与移植思路，支持生成多种预设 Noctis 规则 profiles。
"""

import argparse
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

def parse_clash_payload(content: str) -> List[str]:
    """解析 clash-rules 的 yaml payload 列表为标准域名"""
    domains = []
    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        item = line.lstrip("-").strip().strip("'\"")
        if not item or item.startswith("#"):
            continue
        if item.startswith("+."):
            domains.append("*." + item[2:])
        elif item.startswith("."):
            domains.append("*." + item[1:])
        else:
            domains.append(item)
    return domains

def build_noctis_profile(
    name: str,
    mode: str = "rules",
    rule_order: str = "direct-proxy-block",
    final: str = "proxy",
    block_domains: Optional[List[str]] = None,
    direct_domains: Optional[List[str]] = None,
    proxy_domains: Optional[List[str]] = None,
    block_geosite: Optional[List[str]] = None,
    direct_geosite: Optional[List[str]] = None,
    proxy_geosite: Optional[List[str]] = None,
    block_geoip: Optional[List[str]] = None,
    direct_geoip: Optional[List[str]] = None,
    proxy_geoip: Optional[List[str]] = None,
) -> Dict[str, Any]:
    def dedup(lst):
        return list(dict.fromkeys(lst)) if lst else []

    routing: Dict[str, Any] = {
        "mode": mode,
        "ruleOrder": rule_order,
        "final": final,
        "blockDomains": dedup(block_domains),
        "directDomains": dedup(direct_domains),
        "proxyDomains": dedup(proxy_domains),
    }

    if block_geosite:
        routing["blockGeosite"] = dedup(block_geosite)
    if direct_geosite:
        routing["directGeosite"] = dedup(direct_geosite)
    if proxy_geosite:
        routing["proxyGeosite"] = dedup(proxy_geosite)

    if block_geoip:
        routing["blockGeoip"] = dedup(block_geoip)
    if direct_geoip:
        routing["directGeoip"] = dedup(direct_geoip)
    if proxy_geoip:
        routing["proxyGeoip"] = dedup(proxy_geoip)

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return {
        "kind": "noctis-routing-profile",
        "format": 1,
        "exportedAt": now_iso,
        "name": name,
        "routing": routing
    }

def main():
    parser = argparse.ArgumentParser(description="Build Noctis routing profiles from Loyalsoldier rules")
    parser.add_argument("--fetch-online", action="store_true", help="尝试从 GitHub/CDN 拉取在线规则文件生成展开版")
    parser.add_argument("-o", "--output-dir", default="", help="输出目录")
    args = parser.parse_args()

    out_dir = args.output_dir or os.path.join(os.path.dirname(__file__), "..", "rules_dist")
    os.makedirs(out_dir, exist_ok=True)

    user_direct_domains = [
        "*.oracle.com",
        "*.oraclecloud.com",
        "*.aimatech.com",
        "*.aimaiot.com",
        "*.sotamodel.net",
        "*.aimaiot.com.cn"
    ]
    user_proxy_domains = [
        "play.googleapis.com",
        "95516.com",
        "*.linux.do"
    ]

    print("[1/2] 构建 Noctis 经典白名单 Profile (绕过大陆 + 广告拦截)...")
    whitelist_profile = build_noctis_profile(
        name="noctis-loyalsoldier-whitelist",
        mode="rules",
        rule_order="direct-proxy-block",
        final="proxy",
        block_domains=[],
        direct_domains=user_direct_domains,
        proxy_domains=user_proxy_domains,
        block_geosite=["category-ads-all"],
        direct_geosite=["cn", "apple", "private"],
        proxy_geosite=["geolocation-!cn", "google", "youtube", "telegram", "github"],
        direct_geoip=["cn"]
    )
    whitelist_path = os.path.join(out_dir, "noctis-whitelist.json")
    with open(whitelist_path, "w", encoding="utf-8") as f:
        json.dump(whitelist_profile, f, ensure_ascii=False, indent=2)
    print(f"  -> 生成成功: {whitelist_path}")

    print("[2/2] 构建 Noctis GFW 黑名单 Profile (仅受限服务走代理)...")
    gfw_profile = build_noctis_profile(
        name="noctis-loyalsoldier-gfw",
        mode="rules",
        rule_order="direct-proxy-block",
        final="direct",
        block_domains=[],
        direct_domains=user_direct_domains,
        proxy_domains=user_proxy_domains,
        block_geosite=["category-ads-all"],
        direct_geosite=["cn", "apple", "private"],
        proxy_geosite=["geolocation-!cn", "google", "youtube", "telegram", "github", "twitter", "discord"],
        direct_geoip=["cn"]
    )
    gfw_path = os.path.join(out_dir, "noctis-gfw.json")
    with open(gfw_path, "w", encoding="utf-8") as f:
        json.dump(gfw_profile, f, ensure_ascii=False, indent=2)
    print(f"  -> 生成成功: {gfw_path}")

    print("\n所有 Noctis 规则 profiles 已构建完成！")

if __name__ == "__main__":
    main()
