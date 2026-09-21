# Noctis Rules 增强分流规则集

<p align="center">
  <strong>专为 <a href="https://github.com/c0nn3ct-info/noctis">Noctis</a> 浏览器代理扩展打造的声明式分流规则集</strong><br>
  <em>对齐 <a href="https://github.com/Loyalsoldier/v2ray-rules-dat">Loyalsoldier/v2ray-rules-dat</a> 与 <a href="https://github.com/Loyalsoldier/clash-rules">Loyalsoldier/clash-rules</a> 经典分流策略体系</em>
</p>

---

## 🌟 核心优势

- ⚡ **极致轻量（~1KB）**：拒绝把数万行明文域名塞进扩展存储，浏览器扩展秒开、零卡顿。
- 🔄 **一次导入，终身免维护**：采用声明式分类引用架构，底层数据由 sing-box 自动同步上游二进制 `.srs` 规则库，策略配置无需频繁改动。
- 🛡️ **广告与隐私拦截**：挂载 `category-ads-all` 规则库，自动过滤广告与隐私追踪，触发 Noctis 内置拦截保护页。
- 🌐 **双模全兼容**：深度适配 Noctis，同时完美支持 **URL 在线订阅导入**、**本地文件上传** 与 **JSON 文本粘贴**。
- 🎯 **个性化直连/代理**：内置常用开发及服务直连/代理规则（如 Oracle Cloud、Linux.do、Google Play 等），支持自由定制。

---

## 📥 订阅直链（复制后在 Noctis 直接导入）

| 规则方案 | 策略说明 | 订阅 URL 直链 |
| :--- | :--- | :--- |
| **白名单模式** (`noctis-whitelist.json`) | **⭐ 强烈推荐**。大陆域名/Apple/内网直连，海外流量全走代理，去广告 | `https://raw.githubusercontent.com/gofreehj/noctis-rules/main/rules_dist/noctis-whitelist.json` |
| **GFW 黑名单模式** (`noctis-gfw.json`) | 仅受限核心服务（Google/YouTube/GitHub/TG/Twitter等）走代理，其余默认直连 | `https://raw.githubusercontent.com/gofreehj/noctis-rules/main/rules_dist/noctis-gfw.json` |

---

## 🧭 分流策略逻辑

```text
       流量进入 Noctis
             │
     ┌───────┴───────┐
     ▼               ▼
[直接匹配]       [Geosite/Geoip 规则]
     │               │
     ├─ 广告追踪 ────┼──► 拦截 (Block) ──► 触发 Noctis 拦截页
     ├─ 大陆/Apple ──┼──► 直连 (Direct) ──► 本地网络直连
     ├─ 受限/海外 ───┼──► 代理 (Proxy) ──► 走当前激活的节点
     │               │
     └───────────────┘
             │
         未命中规则 (兜底)
             │
             ├─ 白名单模式 ──► 走代理 (Proxy)
             └─ 黑名单模式 ──► 直连 (Direct)
```

| 分流层级 | 策略配置 | 对应 Loyalsoldier 数据源 | 行为 |
| :--- | :--- | :--- | :--- |
| **广告拦截** | `"blockGeosite": ["category-ads-all"]` | `reject.txt` | 丢弃请求并提示 |
| **内网直连** | `"directGeosite": ["private"]` | `private.txt` / `lancidr.txt` | 局域网私有 IP 域名直连 |
| **大陆直连** | `"directGeosite": ["cn", "apple"]` | `direct.txt` / `apple.txt` | 国内主流网站与 Apple 加速节点直连 |
| **大陆 IP 直连** | `"directGeoip": ["cn"]` | `cncidr.txt` | 大陆 IP 范围直连 |
| **代理服务** | `"proxyGeosite": ["geolocation-!cn", ...]` | `proxy.txt` / `gfw.txt` | 海外站点及核心受限服务走代理 |
| **个性化覆盖** | `"directDomains"` / `"proxyDomains"` | 用户自定义域名列表 | 最高优先级判定 |

---

## 🚀 使用方法

1. 打开 Chrome 扩展 **Noctis**。
2. 点击 **Routing（路由设置）** $\rightarrow$ **Import Profile（导入配置）**。
3. 粘贴上述订阅直链（或将 JSON 文件下载后上传）。
4. 确保运行模式选择为 **Rules** 模式，分流即刻生效。

---

## 🛠️ 本地重新构建或定制

如果需要添加个人专属的域名规则，可直接编辑 `scripts/build_noctis_rules.py` 并运行：

```bash
# 本地生成全兼容配置文件
python scripts/build_noctis_rules.py
```

---

## 📄 许可证

本项目遵循 [MIT License](./LICENSE)。分流数据归各上游项目共同所有。
