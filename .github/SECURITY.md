# Security Policy

The **Kanha-Team** and the **MeowRobot** contributors take the security of this project seriously. We appreciate your efforts to responsibly disclose any security vulnerabilities you find.

---

## 🛡️ Supported Versions

Only the latest release and the current active development branch (`master`) receive security patches and updates.

| Version | Supported | Notes |
| :--- | :---: | :--- |
| `2.x.x` / `master` | ✅ | Active support & security fixes |
| `< 2.0.0` | ❌ | Deprecated. Please update to latest |

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability or exploit within **MeowRoBot**, please follow these steps:

1. **Do NOT open a public GitHub Issue** to report security vulnerabilities, as this exposes active bot deployments to risk before a fix is available.
2. **Private Disclosure**:
   - You can submit a private advisory through [GitHub Security Advisory](https://github.com/Kanha-Team/MeowRobot/security/advisories/new).
   - Alternatively, reach out directly to the maintainers on Telegram:
     - Community Support: [https://t.me/MeowClone](https://t.me/MeowClone)
     - Updates Channel: [https://t.me/MeowCloner](https://t.me/MeowCloner)

### What to Include in Your Report:
- A detailed description of the vulnerability.
- Steps to reproduce the issue (proof-of-concept scripts, message payloads, or steps).
- The potential impact on bot deployments, group chats, or database integrity.
- Any suggested fixes or mitigations (optional).

---

## ⏱️ Response Timeline

- **Initial Acknowledgment**: Within 48 hours of receipt.
- **Assessment & Fix**: We will work on investigating and validating the issue, developing a patch, and deploying a fix.
- **Public Disclosure**: Once patched, we will release a security update and give credit to the researcher (unless anonymity is requested).

---

## 🔒 Security Best Practices for Bot Deployers

- **Never share your Bot Token (`TOKEN`) or API credentials (`API_ID`, `API_HASH`, `MONGO_DB_URI`) publicly.**
- If you accidentally expose sensitive credentials in a public commit or log, immediately revoke and regenerate them:
  - Revoke and regenerate bot tokens via [@BotFather](https://t.me/BotFather).
  - Regenerate MongoDB database credentials on MongoDB Atlas.
- Ensure only trusted administrators are granted elevated permissions (`DRAGONS`, `DEV_USERS`, `DEMONS`).
- Always keep your repository up-to-date with upstream changes on `master`.
