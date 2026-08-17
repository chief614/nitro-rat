# nitro-rat maker
Educational security research tool demonstrating client-side vulnerabilities

# Security Research Tool - Educational Use Only

## ⚠️ DISCLAIMER ⚠️
**This tool is for educational and security research purposes ONLY.**
Unauthorized access to computer systems is illegal. Use this only on systems you own or have explicit written permission to test.

## Description
This project demonstrates how easily users can be tricked into running malicious code disguised as legitimate software. It highlights:
- The importance of verifying software sources
- How browser password managers can be exploited
- The risks of running untrusted code
- Why two-factor authentication is important

## How It Works
1. The builder (`gen.py`) creates a payload
2. The payload appears as a Discord Nitro generator
3. When run, it demonstrates data collection techniques
4. Data is sent to a Discord webhook

## Features
- System information collection
- Browser password extraction
- Session cookie theft
- Discord token extraction
- Wi-Fi password collection
- Screenshot capture

## Requirements
- Python 3.6+
- Windows OS
- Discord webhook URL

## Installation
```bash
pip install -r requirements.txt
