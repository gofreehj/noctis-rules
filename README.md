# Noctis Rules 增强分流规则集

<p align="center">
  <strong>基于 <a href="https://github.com/Loyalsoldier/v2ray-rules-dat">Loyalsoldier/v2ray-rules-dat</a> 与 <a href="https://github.com/Loyalsoldier/clash-rules">Loyalsoldier/clash-rules</a> 移植的 Noctis 路由规则集</strong><br>
  <em>参考 <a href="https://github.com/lyc8503/sing-box-rules">lyc8503/sing-box-rules</a> 的自动化构建思路，通过 GitHub Actions 每日自动构建同步</em>
</p>

---

## 🌟 特性

- 🚀 **开箱即用**：提供标准白名单（绕过大陆 + 广告拦截）与 GFW 黑名单两种经典预设。
- 🔄 **每日自动同步**：GitHub Actions 每天早晨从上游 Loyalsoldier 同步最新规则并自动构建发布。
- 🛡️ **广告与隐私保护**：内置 `category-ads-all` 规则，自动屏蔽常见广告追踪域名并触发 Noctis 拦截提示。
- ⚡ **原生高效**：采用 Noctis 原生 Geosite/Geoip 规则架构，运行时直接编译为 sing-box/mihomo 二进制规则集，省内存、不卡顿。
- 🎯 **个性化融合**：支持将用户自定义的直连/代理域名与上游规则无缝融合。

---

## 📥 规则文件直链（右键另存为或直接在 Noctis 导入）

| 规则名称 | 适用场景 | 直链下载地址 |
| :--- | :--- | :--- |
| **白名单模式** (`noctis-whitelist.json`) | **推荐**。大陆网站/Apple/局域网直连，海外网站全走代理，去广告 | [点击下载](https://raw.githubusercontent.com/gofreehj/noctis-rules/main/rules_dist/noctis-whitelist.json) |
| **GFW 黑名单模式** (`noctis-gfw.json`) | 仅 Google/YouTube/GitHub/TG 等被限制服务走代理，其余默认直连 | [点击下载](https://raw.githubusercontent.com/gofreehj/noctis-rules/main/rules_dist/noctis-gfw.json) |

---

## 🧭 规则分流映射设计

| 分流层级 | Loyalsoldier 规则集 (`clash-rules` / `v2ray-rules-dat`) | Noctis 对应字段 | 效果 |
| :--- | :--- | :--- | :--- |
| **广告拦截** | `reject.txt` / `category-ads-all` | `"blockGeosite": ["category-ads-all"]` | 广告/隐私追踪直接拦截 |
| **内网直连** | `private.txt` / `lancidr.txt` | `"directGeosite": ["private"]` | 局域网及私有 IP 域名直连 |
| **大陆直连** | `direct.txt` (`cn`), `apple.txt` | `"directGeosite": ["cn", "apple"]` | 国内百万级主流域名与 Apple 服务直连 |
| **大陆 IP 直连** | `cncidr.txt` (`geoip:cn`) | `"directGeoip": ["cn"]` | 国内 IP 范围直连 |
| **代理服务** | `proxy.txt` (`geolocation-!cn`), `gfw.txt` | `"proxyGeosite": ["geolocation-!cn", ...]` | 海外站点及核心受限服务走代理 |
| **用户自定义** | 自定义域名列表 | `"directDomains"` / `"proxyDomains"` | 最高优先级覆盖 |

---

## 🚀 使用方法

1. 打开 Chrome 扩展 **Noctis**。
2. 点击 **Routing（路由设置）** $\rightarrow$ **Import Profile（导入配置）**。
3. 选择下载好的 `noctis-whitelist.json` 或粘贴 JSON 内容。
4. 确保运行模式处于 **Rules** 模式，分流即刻生效。

---

## 🛠️ 本地构建与定制

你可以在本地运行脚本重新生成或定制自己的规则：

```bash
# 生成默认规则
python scripts/build_noctis_rules.py

# 从已有 sing-box 配置文件转换导入
python scripts/port_singbox_rules_to_noctis.py --input-singbox /path/to/singbox.json -o custom-noctis.json
```

---

## 📄 开源许可

本项目遵循 [MIT License](./LICENSE)。规则数据源版权归原项目所有。
