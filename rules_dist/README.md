# Loyalsoldier Rules for Noctis (Noctis 分流规则移植集)

本项目将 [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat) 与 [Loyalsoldier/clash-rules](https://github.com/Loyalsoldier/clash-rules) 的全量分流规则移植到 **Noctis** 浏览器代理扩展。

参考 `lyc8503/sing-box-rules` 的自动化构建与移植思想，本项目提供开箱即用的 Noctis 路由配置文件，并可通过 GitHub Actions 保持每天与上游规则同步。

---

## 配置文件列表

| 配置文件 | 分流策略 | 适用场景 |
| :--- | :--- | :--- |
| [`noctis-whitelist.json`](./noctis-whitelist.json) | **经典白名单模式**（绕过大陆 + 广告拦截） | 推荐：大陆网站/Apple/局域网直连，其余海外站点走代理 |
| [`noctis-gfw.json`](./noctis-gfw.json) | **GFW 黑名单模式** | 仅被墙站点（Google/YouTube/TG/GitHub等）走代理，其余默认直连 |

---

## 规则映射表

| Loyalsoldier 规则集 | Noctis Profile 配置 | 底层 sing-box / mihomo 行为 |
| :--- | :--- | :--- |
| `reject.txt` (`category-ads-all`) | `"blockGeosite": ["category-ads-all"]` | 广告/隐私追踪直接丢弃并显示 Noctis Block 页面 |
| `direct.txt` (`geosite:cn`) | `"directGeosite": ["cn"]` | 国内百万级主流域名走原生直连 |
| `apple.txt` | `"directGeosite": ["apple"]` | Apple 大陆加速节点直连 |
| `private.txt` (`lancidr.txt`) | `"directGeosite": ["private"]` | 局域网/内网域名与 IP 直连 |
| `cncidr.txt` (`geoip:cn`) | `"directGeoip": ["cn"]` | 中国大陆 IP 范围直连 |
| `proxy.txt` (`geolocation-!cn`) | `"proxyGeosite": ["geolocation-!cn"]` | 非大陆海外站点走代理通道 |
| `gfw.txt` | 对应核心受限服务标签 | 受限核心服务走代理通道 |
| 用户个性化域名 | `"directDomains"` / `"proxyDomains"` | 优先最高级别判定 |

---

## 导入与使用方式

1. 打开 Chrome 扩展中的 **Noctis**。
2. 点击 **Routing（路由 / 规则）**。
3. 选择 **Import Profile**，导入本目录下的 `noctis-whitelist.json` 或 `noctis-gfw.json`。
4. 确保运行模式选择为 **Rules** 模式即可。
