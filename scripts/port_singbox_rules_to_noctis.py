#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
port_singbox_rules_to_noctis.py
将 sing-box-rules (lyc8503) 与 clash-rules (Loyalsoldier) 规则转换/移植为 Noctis 路由配置 (noctis-routing-profile)。

使用示例:
  1. 生成经典白名单分流配置 (绕过大陆 + 广告拦截 + 用户自定义域名):
     python scripts/port_singbox_rules_to_noctis.py --preset whitelist -o noctis-whitelist.json

  2. 生成 GFWList 黑名单分流配置 (黑名单走代理，其余直连):
     python scripts/port_singbox_rules_to_noctis.py --preset gfw -o noctis-gfw.json

  3. 从 sing-box JSON 配置文件中迁移 rules:
     python scripts/port_singbox_rules_to_noctis.py --input-singbox /path/to/singbox.json -o noctis-imported.json

  4. 从 Loyalsoldier/clash-rules 的 rule-provider YAML 文件中导入域名:
     python scripts/port_singbox_rules_to_noctis.py --import-clash-file apple.txt --target direct -o noctis-with-apple.json
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

# Noctis 官方扩展所支持的 Geosite 与 Geoip 分类 (见 Noctis sidepanel/load 模块)
NOCTIS_SUPPORTED_GEOSITES = {
    "cn", "geolocation-cn", "geolocation-!cn", "category-ru",
    "category-ads", "category-ads-all", "category-porn", "private",
    "apple", "microsoft", "google", "google-play", "youtube", "github",
    "gitlab", "twitter", "facebook", "instagram", "tiktok", "telegram",
    "whatsapp", "discord", "netflix", "spotify", "steam", "epicgames",
    "riot", "escapefromtarkov", "twitch", "pinterest", "faceit",
    "cloudflare", "amazon", "reddit", "4chan"
}

NOCTIS_SUPPORTED_GEOIPS = {
    "cn", "us", "jp", "hk", "sg", "ru", "de", "gb", "fr", "tw", "kr"
}

def clean_tag(raw: str) -> str:
    """清理 geosite: 或 geoip: 前缀"""
    s = raw.strip().lower()
    s = re.sub(r'^(geosite|geoip)[:-]', '', s)
    return s

def clean_domain(domain: str) -> str:
    """清理并标准化域名格式"""
    d = domain.strip().lower()
    d = re.sub(r'^https?://', '', d)
    d = d.split('/')[0].split(':')[0]
    return d

def parse_clash_payload_line(line: str) -> Optional[str]:
    """解析 Clash rule-provider yaml 中的 payload 域名"""
    l = line.strip()
    if not l.startswith('-'):
        return None
    item = l.lstrip('-').strip().strip("'\"")
    if not item or item.startswith('#'):
        return None
    # Clash 格式如 '+.example.com' 或 '.example.com' 对应通配符
    if item.startswith('+.'):
        return '*.' + item[2:]
    if item.startswith('.'):
        return '*.' + item[1:]
    return item

def generate_noctis_profile(
    name: str = "singbox-rules-ported",
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
    """生成符合 Noctis 规范的 routing profile 结构"""
    def ensure_list(val):
        return list(dict.fromkeys(val)) if val else []

    routing: Dict[str, Any] = {
        "mode": mode,
        "ruleOrder": rule_order,
        "final": final,
        "blockDomains": ensure_list(block_domains),
        "directDomains": ensure_list(direct_domains),
        "proxyDomains": ensure_list(proxy_domains),
    }

    if block_geosite:
        routing["blockGeosite"] = ensure_list(block_geosite)
    if direct_geosite:
        routing["directGeosite"] = ensure_list(direct_geosite)
    if proxy_geosite:
        routing["proxyGeosite"] = ensure_list(proxy_geosite)

    if block_geoip:
        routing["blockGeoip"] = ensure_list(block_geoip)
    if direct_geoip:
        routing["directGeoip"] = ensure_list(direct_geoip)
    if proxy_geoip:
        routing["proxyGeoip"] = ensure_list(proxy_geoip)

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return {
        "kind": "noctis-routing-profile",
        "format": 1,
        "exportedAt": now_iso,
        "name": name,
        "routing": routing
    }

def convert_singbox_config(config_json: Dict[str, Any], name: str = "singbox-migrated") -> Dict[str, Any]:
    """从 sing-box 完整配置或 route 块中解析并移植到 Noctis 规则"""
    route = config_json.get("route", config_json)
    rules = route.get("rules", [])

    block_domains: Set[str] = set()
    direct_domains: Set[str] = set()
    proxy_domains: Set[str] = set()

    block_geosite: Set[str] = set()
    direct_geosite: Set[str] = set()
    proxy_geosite: Set[str] = set()

    block_geoip: Set[str] = set()
    direct_geoip: Set[str] = set()
    proxy_geoip: Set[str] = set()

    for r in rules:
        action = r.get("action", "")
        outbound = r.get("outbound", "").lower()
        if action in ["sniff", "hijack-dns", "resolve"]:
            continue

        target = "proxy"
        if action in ["reject", "block"] or outbound in ["block", "reject"]:
            target = "block"
        elif outbound in ["direct", "bypass"]:
            target = "direct"

        dom_target = direct_domains if target == "direct" else block_domains if target == "block" else proxy_domains
        gs_target = direct_geosite if target == "direct" else block_geosite if target == "block" else proxy_geosite
        gi_target = direct_geoip if target == "direct" else block_geoip if target == "block" else proxy_geoip

        for k in ["domain", "domain_suffix"]:
            vals = r.get(k, [])
            if isinstance(vals, str):
                vals = [vals]
            for v in vals:
                dom = v.strip()
                if k == "domain_suffix" and not dom.startswith("*."):
                    dom = "*." + dom.lstrip(".")
                dom_target.add(dom)

        gs_list = r.get("geosite", [])
        if isinstance(gs_list, str):
            gs_list = [gs_list]
        for g in gs_list:
            cleaned = clean_tag(g)
            if cleaned in NOCTIS_SUPPORTED_GEOSITES:
                gs_target.add(cleaned)

        gi_list = r.get("geoip", [])
        if isinstance(gi_list, str):
            gi_list = [gi_list]
        for gi in gi_list:
            cleaned = clean_tag(gi)
            if cleaned in NOCTIS_SUPPORTED_GEOIPS:
                gi_target.add(cleaned)

        rs_list = r.get("rule_set", [])
        if isinstance(rs_list, str):
            rs_list = [rs_list]
        for tag in rs_list:
            if tag.startswith("geosite-"):
                name_tag = tag.replace("geosite-", "")
                if name_tag in NOCTIS_SUPPORTED_GEOSITES:
                    gs_target.add(name_tag)
            elif tag.startswith("geoip-"):
                name_tag = tag.replace("geoip-", "")
                if name_tag in NOCTIS_SUPPORTED_GEOIPS:
                    gi_target.add(name_tag)

    final_action = route.get("final", "proxy").lower()
    final = "direct" if final_action in ["direct", "bypass"] else "proxy"

    return generate_noctis_profile(
        name=name,
        mode="rules",
        rule_order="direct-proxy-block",
        final=final,
        block_domains=list(block_domains),
        direct_domains=list(direct_domains),
        proxy_domains=list(proxy_domains),
        block_geosite=list(block_geosite),
        direct_geosite=list(direct_geosite),
        proxy_geosite=list(proxy_geosite),
        block_geoip=list(block_geoip),
        direct_geoip=list(direct_geoip),
        proxy_geoip=list(proxy_geoip),
    )

def create_preset_profile(preset: str, user_direct: List[str], user_proxy: List[str], name: str) -> Dict[str, Any]:
    if preset == "gfw":
        # 黑名单模式 (仅被封锁服务走代理，其余直连)
        return generate_noctis_profile(
            name=name or "noctis-gfw-rules",
            mode="rules",
            rule_order="direct-proxy-block",
            final="direct",
            block_domains=[],
            direct_domains=user_direct,
            proxy_domains=user_proxy,
            block_geosite=["category-ads-all"],
            direct_geosite=["cn", "apple", "private"],
            proxy_geosite=["geolocation-!cn", "google", "youtube", "telegram", "github", "twitter", "discord"],
            direct_geoip=["cn"],
            proxy_geoip=[]
        )
    else:
        # 白名单模式 (绕过局域网与大陆，其余走代理)
        return generate_noctis_profile(
            name=name or "noctis-whitelist-rules",
            mode="rules",
            rule_order="direct-proxy-block",
            final="proxy",
            block_domains=[],
            direct_domains=user_direct,
            proxy_domains=user_proxy,
            block_geosite=["category-ads-all"],
            direct_geosite=["cn", "apple", "private"],
            proxy_geosite=["geolocation-!cn", "google", "youtube", "telegram", "github"],
            direct_geoip=["cn"],
            proxy_geoip=[]
        )

def main():
    parser = argparse.ArgumentParser(description="Port sing-box-rules and clash-rules to Noctis routing profile")
    parser.add_argument("--preset", choices=["whitelist", "gfw"], default="whitelist", help="预设模式 (whitelist: 绕过大陆, gfw: 黑名单模式)")
    parser.add_argument("--input-singbox", help="输入现有 sing-box JSON 配置文件路径进行迁移")
    parser.add_argument("--import-clash-file", help="输入 Loyalsoldier/clash-rules 的 txt/yaml 规则文件路径")
    parser.add_argument("--target", choices=["direct", "proxy", "block"], default="direct", help="导入 clash 文件条目的目标分类 (direct/proxy/block)")
    parser.add_argument("--name", default="noctis-rules", help="Profile 规则名称")
    parser.add_argument("-o", "--output", help="输出 JSON 规则文件路径")

    args = parser.parse_args()

    default_user_direct = [
        "*.oracle.com",
        "*.oraclecloud.com",
        "*.aimatech.com",
        "*.aimaiot.com",
        "*.sotamodel.net",
        "*.aimaiot.com.cn"
    ]
    default_user_proxy = [
        "play.googleapis.com",
        "95516.com",
        "*.linux.do"
    ]

    if args.input_singbox:
        if not os.path.exists(args.input_singbox):
            print(f"Error: input file '{args.input_singbox}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(args.input_singbox, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        profile = convert_singbox_config(cfg, name=args.name)
    elif args.import_clash_file:
        if not os.path.exists(args.import_clash_file):
            print(f"Error: clash file '{args.import_clash_file}' not found.", file=sys.stderr)
            sys.exit(1)
        imported_domains = []
        with open(args.import_clash_file, "r", encoding="utf-8") as f:
            for line in f:
                d = parse_clash_payload_line(line)
                if d:
                    imported_domains.append(d)
        
        direct_doms = list(default_user_direct)
        proxy_doms = list(default_user_proxy)
        block_doms = []

        if args.target == "direct":
            direct_doms.extend(imported_domains)
        elif args.target == "proxy":
            proxy_doms.extend(imported_domains)
        elif args.target == "block":
            block_doms.extend(imported_domains)

        profile = generate_noctis_profile(
            name=args.name,
            mode="rules",
            rule_order="direct-proxy-block",
            final="proxy",
            block_domains=block_doms,
            direct_domains=direct_doms,
            proxy_domains=proxy_doms,
            block_geosite=["category-ads-all"],
            direct_geosite=["cn", "apple", "private"],
            proxy_geosite=["geolocation-!cn"],
            direct_geoip=["cn"]
        )
    else:
        profile = create_preset_profile(args.preset, default_user_direct, default_user_proxy, args.name)

    output_json = json.dumps(profile, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
        print(f"Profile saved to: {args.output}")
    else:
        print(output_json)

if __name__ == "__main__":
    main()
