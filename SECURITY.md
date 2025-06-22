# 安全政策 🔒

## 支持的版本

我们目前支持以下版本的安全更新：

| 版本 | 支持状态 |
| --- | --- |
| 1.x.x | ✅ |
| < 1.0 | ❌ |

## 报告安全漏洞

如果你发现了安全漏洞，请**不要**在公开的GitHub Issues中报告。

### 报告方式

1. **私人邮箱报告**（推荐）
   - 发送邮件至：security@example.com
   - 主题格式：`[SECURITY] WordNest 安全漏洞报告`

2. **GitHub私人报告**
   - 使用GitHub的安全漏洞报告功能
   - 在仓库页面点击"Security" → "Report a vulnerability"

### 报告内容

请在报告中包含以下信息：

- **漏洞类型**：XSS、SQL注入、权限绕过等
- **影响范围**：哪些功能受影响
- **重现步骤**：详细的复现步骤
- **环境信息**：操作系统、Python版本、浏览器等
- **概念验证**：如果可能，提供PoC代码
- **修复建议**：如果有修复思路请提供

### 响应时间承诺

我们承诺：

- **24小时内**：确认收到报告
- **7天内**：提供初步分析和风险评估
- **30天内**：发布修复版本（视漏洞复杂度而定）

## 安全最佳实践

### 部署建议

1. **环境变量**
   ```bash
   # 使用强密码作为SECRET_KEY
   SECRET_KEY=your-very-strong-secret-key-here
   
   # 不要在生产环境中启用调试模式
   FLASK_DEBUG=False
   ```

2. **数据库安全**
   ```bash
   # 使用专用数据库用户
   DATABASE_URI=sqlite:///secure_path/words.db
   
   # 定期备份数据
   ```

3. **网络安全**
   ```bash
   # 使用HTTPS（生产环境）
   # 配置防火墙规则
   # 使用反向代理（如Nginx）
   ```

### 代码安全

1. **输入验证**
   - 所有用户输入都应进行验证
   - 防止XSS攻击：对HTML内容进行转义
   - 防止SQL注入：使用参数化查询

2. **会话管理**
   - 使用安全的会话配置
   - 设置合适的会话超时时间
   - 使用CSRF保护

3. **文件安全**
   - 验证上传文件类型和大小
   - 将上传文件存储在安全位置
   - 不执行用户上传的代码

### 依赖安全

1. **定期更新**
   ```bash
   # 检查依赖漏洞
   pip audit
   
   # 更新依赖
   pip install --upgrade -r requirements.txt
   ```

2. **漏洞扫描**
   ```bash
   # 安装safety工具
   pip install safety
   
   # 扫描已知漏洞
   safety check
   ```

## 已知安全注意事项

### API密钥管理

⚠️ **重要**：项目中包含AI功能，需要API密钥

- 绝对不要在代码中硬编码API密钥
- 使用环境变量存储敏感信息
- 定期轮换API密钥
- 监控API密钥使用情况

### 数据保护

- 数据库文件包含用户学习数据
- 建议定期备份重要数据
- 在生产环境中使用加密存储

### 网络请求

- AI功能会向外部API发送请求
- 确保HTTPS连接的安全性
- 监控异常的网络活动

## 安全更新

### 自动更新

我们建议启用依赖的安全更新：

```bash
# 使用pip-audit检查漏洞
pip install pip-audit
pip-audit

# 使用Dependabot（GitHub功能）
# 在仓库设置中启用Dependabot alerts
```

### 手动检查

定期执行安全检查：

```bash
# 检查Python包漏洞
safety check

# 检查代码质量
bandit -r app.py models.py

# 检查依赖许可证
pip-licenses
```

## 安全功能

### 当前安全措施

- ✅ CSRF保护
- ✅ SQL注入防护（使用ORM）
- ✅ XSS防护（模板自动转义）
- ✅ 会话安全
- ✅ 输入验证

### 计划中的安全改进

- 🔄 添加速率限制
- 🔄 实现用户认证
- 🔄 添加审计日志
- 🔄 实现文件上传安全检查

## 联系信息

- **安全团队邮箱**：security@example.com
- **项目维护者**：[@wink-wink-wink555](https://github.com/wink-wink-wink555)
- **安全讨论区**：[GitHub Discussions](https://github.com/wink-wink-wink555/WordNest/discussions)

## 致谢

感谢以下安全研究人员的贡献：

<!-- 这里会列出报告安全漏洞的研究人员 -->
- 暂无

---

**注意**：安全是一个持续的过程。我们会不断改进项目的安全性，并感谢社区的安全研究人员的贡献。 