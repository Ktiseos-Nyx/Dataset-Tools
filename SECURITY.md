# Security Policy for Dataset-Tools

Hello! We're Ktiseos Nyx, and we take the security of Dataset-Tools seriously. As an open-source project, we believe in transparency and welcome the community's help in keeping our software safe. If you think you've found a security vulnerability, please let us know!

## Our Commitment

* We aim to address security vulnerabilities in a timely manner, prioritizing them based on their potential impact.
* We will be transparent about vulnerabilities and our efforts to fix them, following responsible disclosure practices.
* We strive to use secure coding practices and keep our dependencies up-to-date.

## Supported Versions & Development Status

Dataset-Tools is under active development.

* **Currently Supported Version:** The `main` branch always represents the latest development version and is the primary focus for new features, bug fixes, and security updates. We encourage all users to use the latest state of the `main` branch.
* **Release Tags (Future):** As we begin to make formal releases (e.g., v0.6.0, v1.0.0), we will clearly define which tagged releases are actively supported with security patches. For now, `main` is key.
* **Older Development States/Branches:** Branches or tags representing development states significantly older than the current `main` (e.g., pre-v0.58 series or unmaintained feature branches) are considered unsupported and may not receive security updates.

We are committed to providing security support for the current development version (`main` branch) and will define support for tagged releases as they are made.

## Reporting a Vulnerability

Found a security issue? Thank you for helping us! Please report it to us **privately** so we can address it before it becomes public knowledge.

**🔒 Preferred Method: GitHub Security Advisories**
This is the best and most secure way:

1. Go to the "Security" tab of the [Dataset-Tools GitHub repository](https://github.com/Ktiseos-Nyx/Dataset-Tools).
2. Click on "Advisories."
3. Click "New draft security advisory."
This creates a private space for us to discuss and fix the issue.

**⚠️ Please DO NOT open a regular public GitHub issue for security vulnerabilities.**

**Alternative Reporting Methods (if GitHub Advisories aren't possible):**

* **Discord:** Send a direct message (DM) to a project maintainer (e.g., Ktiseos Nyx) on our official [Discord server](https://discord.gg/HhBSvM9gBY). *Please do not post vulnerability details in public channels.*
* **Email:** (Optional: If you decide to include an email, list it here, e.g., `security@example.com`. Otherwise, you can state: "Email reporting is not preferred for security issues; please use GitHub Advisories or Discord DMs.")

**What to Include in Your Report:**
To help us understand and fix the issue quickly, please include:

* A clear description of the vulnerability.
* Steps to reproduce it (be as detailed as possible).
* Which version/branch of Dataset-Tools is affected.
* The potential impact if the vulnerability is exploited.
* Any proof-of-concept code (if you have it and it's safe to share).
* Your environment details (OS, Python version) if relevant.

We'll do our best to acknowledge your report within 48-72 hours. As an independent project, timelines for fixes will vary based on complexity and severity, but we are committed to addressing confirmed vulnerabilities.

## Our Security Practices

* **Code Review:** We review code changes for potential security issues.
* **Dependency Management:** We aim to keep our third-party libraries up-to-date. We use tools like:
  * **`pip-audit`** (or **`Safety CLI`**) to check our dependencies against known vulnerability databases.
  * **GitHub's Dependabot alerts** (if enabled) to notify us of vulnerable dependencies.
* **Static Analysis:** We use linters and static analysis tools to identify potential issues in our own codebase:
  * **`Ruff`** for general linting, style enforcement, and identifying many common code issues.
  * **`Bandit`** for finding common security pitfalls in Python code.
  * We are also exploring the use of **`Mypy`** for static type checking to improve code robustness.
* **Vendored Code:** Code vendored from other projects (like components from `sd-prompt-reader`) is included with clear attribution and its original license. We take on the responsibility of maintaining or updating these components as needed within our project. See our `NOTICE.md` file for details.

We are always looking to improve our security posture and appreciate community feedback on our practices.

## Licensing

Dataset-Tools is licensed under the **GNU General Public License v3.0 or later (GPL-3.0-or-later)**. The full text of this license can be found in the [LICENSE](LICENSE) file in the root of this repository.

Our use of any third-party libraries or vendored code is done in compliance with their respective licenses (details in `NOTICE.md`).

---
