#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_noctis_rules.py
将 Loyalsoldier/clash-rules 和 Loyalsoldier/v2ray-rules-dat 移植为 Noctis 专属分流规则集。
实现真正的白名单分流 (国内直连 + 广告拦截 + 其余海外未收录域名全走代理)。
"""

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

def build_noctis_profile(
    name: str,
    mode: str = "rules",
    rule_order: str = "block-direct-proxy",
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

        # 全兼容字段
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

    # 1. 白名单模式 (True Whitelist):
    # 规则优先级: 拦截(block) -> 直连(direct) -> 代理(proxy)
    # 通过在 proxyDomains 增加 '*' 通配符，捕获所有未被 geosite:cn 命中的海外/未知域名，
    # 彻底解决小众国外网站 (如 elysiver.h-e.top, api.justwoker.icu) 因未收录在 geolocation-!cn 而被误走直连打不开的问题。
    user_proxy_domains_whitelist = [
        "play.googleapis.com",
        "95516.com",
        "*.linux.do",
        "*"  # 关键修复: 兜底代理通配符
    ]

    print("[1/2] 构建 Noctis 真正的白名单 Profile (拦截广告 -> 国内直连 -> 其余海外全代理)...")
    whitelist_profile = build_noctis_profile(
        name="noctis-loyalsoldier-whitelist",
        mode="rules",
        rule_order="block-direct-proxy",
        final="proxy",
        block_domains=[],
        direct_domains=user_direct_domains,
        proxy_domains=user_proxy_domains_whitelist,
        block_geosite=["category-ads-all"],
        direct_geosite=["cn", "apple", "private"],
        proxy_geosite=["geolocation-!cn", "google", "youtube", "telegram", "github"],
        direct_geoip=["cn"]
    )
    whitelist_path = os.path.join(out_dir, "noctis-whitelist.json")
    with open(whitelist_path, "w", encoding="utf-8") as f:
        json.dump(whitelist_profile, f, ensure_ascii=False, indent=2)
    print(f"  -> 生成成功: {whitelist_path}")

    # 2. GFW 黑名单模式 (仅受限服务走代理，其余直连)
    user_proxy_domains_gfw = [
        "play.googleapis.com",
        "95516.com",
        "*.linux.do"
    ]
    print("[2/2] 构建 Noctis GFW 黑名单 Profile (仅受限服务走代理)...")
    gfw_profile = build_noctis_profile(
        name="noctis-loyalsoldier-gfw",
        mode="rules",
        rule_order="direct-proxy-block",
        final="direct",
        block_domains=[],
        direct_domains=user_direct_domains,
        proxy_domains=user_proxy_domains_gfw,
        block_geosite=["category-ads-all"],
        direct_geosite=["cn", "apple", "private"],
        proxy_geosite=["geolocation-!cn", "google", "youtube", "telegram", "github", "twitter", "discord"],
        direct_geoip=["cn"]
    )
    gfw_path = os.path.join(out_dir, "noctis-gfw.json")
    with open(gfw_path, "w", encoding="utf-8") as f:
        json.dump(gfw_profile, f, ensure_ascii=False, indent=2)
    print(f"  -> 生成成功: {gfw_path}")

    print("\n所有修复后的 Noctis profiles 已构建完成！")

if __name__ == "__main__":
    main()
