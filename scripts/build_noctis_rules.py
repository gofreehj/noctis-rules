#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_noctis_rules.py
将 Loyalsoldier/clash-rules 和 Loyalsoldier/v2ray-rules-dat 移植为 Noctis 专属分流规则集。
同时支持 Noctis 本地文件导入 (noctis-routing-profile) 与 URL 在线订阅导入 (Happ / sing-box schema)。
"""

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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

    b_doms = dedup(block_domains)
    d_doms = dedup(direct_domains)
    p_doms = dedup(proxy_domains)

    b_gs = dedup(block_geosite)
    d_gs = dedup(direct_geosite)
    p_gs = dedup(proxy_geosite)

    b_gi = dedup(block_geoip)
    d_gi = dedup(direct_geoip)
    p_gi = dedup(proxy_geoip)

    # 1. Noctis 原生本地文件/粘贴导入结构 (noctis-routing-profile)
    routing: Dict[str, Any] = {
        "mode": mode,
        "ruleOrder": rule_order,
        "final": final,
        "blockDomains": b_doms,
        "directDomains": d_doms,
        "proxyDomains": p_doms,
    }

    if b_gs:
        routing["blockGeosite"] = b_gs
    if d_gs:
        routing["directGeosite"] = d_gs
    if p_gs:
        routing["proxyGeosite"] = p_gs

    if b_gi:
        routing["blockGeoip"] = b_gi
    if d_gi:
        routing["directGeoip"] = d_gi
    if p_gi:
        routing["proxyGeoip"] = p_gi

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    # 2. Noctis URL 订阅导入结构 (Happ 协议兼容字段)
    # Noctis 扩展的 service_worker 在 import-from-url 时检查这些字段
    direct_sites = list(d_doms) + [f"geosite:{g}" for g in d_gs]
    proxy_sites = list(p_doms) + [f"geosite:{g}" for g in p_gs]
    block_sites = list(b_doms) + [f"geosite:{g}" for g in b_gs]
    direct_ips = [f"geoip:{g}" for g in d_gi]
    proxy_ips = [f"geoip:{g}" for g in p_gi]
    block_ips = [f"geoip:{g}" for g in b_gi]

    return {
        "kind": "noctis-routing-profile",
        "format": 1,
        "exportedAt": now_iso,
        "name": name,
        "routing": routing,

        # 全兼容字段 (解决 URL 导入报 "Response has no routing data" 的问题)
        "Name": name,
        "GlobalProxy": (mode == "global"),
        "RouteOrder": rule_order,
        "DirectSites": direct_sites,
        "ProxySites": proxy_sites,
        "BlockSites": block_sites,
        "DirectIp": direct_ips,
        "ProxyIp": proxy_ips,
        "BlockIp": block_ips
    }

def main():
    parser = argparse.ArgumentParser(description="Build Noctis routing profiles from Loyalsoldier rules")
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

    print("\n所有全兼容 Noctis profiles 已构建完成！")

if __name__ == "__main__":
    main()
