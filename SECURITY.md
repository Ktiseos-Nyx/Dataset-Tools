# Security Policy

At Ktiseos Nyx, we take security seriously. While Dataset-Tools is currently under active development and not yet at a stable release (version 1.0), we are committed to addressing security vulnerabilities promptly and transparently.  We appreciate the community's help in identifying and reporting potential issues.

## Supported Versions & Development Status

Dataset-Tools is currently in an early stage of development.  We are not providing long-term support (LTS) for specific versions at this time.  Our primary focus is on the `main` branch, which represents the latest development state.  We encourage users to use the `main` branch for the most up-to-date features and security improvements.

Older branches (e.g., `0.51`, `0.55`) may exist for historical purposes or to provide a snapshot of previous development states.  While we will make reasonable efforts to address *critical* security issues in these older branches, our primary focus remains on the `main` branch.  Branches older than `0.51` are considered unsupported and may not receive security updates.

**We do not recommend using pre-0.55 versions in production environments.** These versions are intended for testing, development, and community feedback.

## Reporting a Vulnerability

If you discover a potential security vulnerability in Dataset-Tools, please report it to us *privately* before disclosing it publicly. This allows us to address the issue and protect users.

**Preferred Reporting Method:**

*   **Create a security advisory on GitHub:** This is the *best* way to report a vulnerability. Go to the "Security" tab in the repository, then click "Advisories," and then "New draft security advisory." This creates a private space where we can discuss the issue and coordinate a fix. GitHub's built-in security advisory system is designed for this purpose.
* **DO NOT CREATE A REGULAR GITHUB ISSUE.** Regular issues are public.

**Alternative Reporting Methods (if you cannot use a GitHub security advisory):**

*   **Discord (Server, not DM):**  Send a direct message to a project maintainer on our [Discord server](https://discord.gg/HhBSvM9gBY). *Do not post vulnerability details in public channels.*
*  **[IF YOU HAVE EMAIL] Email:** you *can* use email but it is **not** recommended.

**What to Include in Your Report:**

*   **Description of the vulnerability:** Be as detailed as possible.
*   **Steps to reproduce the vulnerability:** Provide clear and concise instructions on how to reproduce the issue.
*   **Affected versions:** Specify which branches or versions of the project are affected.
*   **Potential impact:** Describe the potential consequences of exploiting the vulnerability.
*   **Proof-of-concept (PoC) code (if available):**  This can be very helpful, but ensure the PoC is safe and doesn't cause harm.

We will acknowledge receipt of your report, we will try and work on it within reasonable time but this is indeed an independent study project, and will keep you informed of our progress in addressing the vulnerability. We aim to release a fix as quickly as possible, depending on the severity of the issue.

## Dependency Management and Security Practices

We are committed to using secure coding practices and regularly reviewing our dependencies for known vulnerabilities. We utilize tools like [mention specific tools, e.g., Dependabot, Snyk, OWASP Dependency-Check] to help identify and mitigate potential risks.

We understand that perfect security is an ongoing process, and we strive to continuously improve our practices. We appreciate the community's vigilance and collaboration in helping us maintain a secure project.
We adhere strictly to the [MIT License](https://github.com/Ktiseos-Nyx/Dataset-Tools/blob/main/LICENSE)
