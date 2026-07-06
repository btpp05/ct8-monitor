#!/usr/bin/env python3
"""
CT8 注册队列监控脚本
单次运行版（适合 GitHub Actions 定时执行）
监控 https://ct8.00666.xyz 队列状态，有位置时通知并注册
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

# ========== 配置 ==========
API_URL = "https://ct8.00666.xyz"
MAX_RETRIES = 3

# 要注册的邮箱（环境变量，逗号分隔）
EMAILS_STR = os.environ.get("CT8_EMAILS", "ohjustb@outlook.com,hubtpp@gmail.com,acehhlmm@gmail.com")
EMAILS = [e.strip() for e in EMAILS_STR.split(",") if e.strip()]

# Telegram 通知
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

# 状态文件（GitHub Actions 通过 artifact 或 cache 持久化）
STATUS_FILE = "/tmp/ct8_status.json"
REGISTERED_FILE = "/tmp/ct8_registered.json"


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def send_tg(text):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    try:
        payload = json.dumps({
            "chat_id": TG_CHAT_ID,
            "text": text,
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
        log("✅ Telegram 通知已发送")
    except Exception as e:
        log(f"❌ Telegram 发送失败: {e}")


def build_opener():
    """创建支持代理的 opener"""
    proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy") or os.environ.get("HTTPS_PROXY")
    if proxy:
        proxy_support = urllib.request.ProxyHandler({
            "http": proxy,
            "https": proxy,
        })
        return urllib.request.build_opener(proxy_support)
    return urllib.request.build_opener()


def get_status():
    try:
        opener = build_opener()
        resp = opener.open(f"{API_URL}/api/status", timeout=15)
        return json.loads(resp.read().decode())
    except Exception as e:
        log(f"❌ 获取状态失败: {e}")
        return None


def add_email(email):
    try:
        opener = build_opener()
        data = urllib.parse.urlencode({"email": email}).encode()
        req = urllib.request.Request(
            f"{API_URL}/api/add_email",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp = opener.open(req, timeout=15)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"success": False, "message": f"请求失败: {e}"}


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


def main():
    log("=" * 40)
    log("CT8 注册队列监控")
    log(f"要注册的邮箱: {EMAILS}")
    log("=" * 40)

    last_slots = load_json(STATUS_FILE, {"slots_available": -1})
    registered = set(load_json(REGISTERED_FILE, []))

    status = get_status()
    if not status:
        sys.exit(1)

    enabled = status.get("enabled", False)
    slots_avail = status.get("slots_available", 0)
    queue = status.get("queue", 0)
    success = status.get("success", 0)
    slots_total = status.get("slots_total", 0)

    log(f"队列开启: {'✅' if enabled else '❌'} | "
        f"剩余席位: {slots_avail}/{slots_total} | "
        f"队列: {queue} | 已成功: {success}")

    prev_slots = last_slots.get("slots_available", -1)
    save_json(STATUS_FILE, {"slots_available": slots_avail})

    # 有位置且队列开启
    if enabled and slots_avail > 0:
        # 位置有变化才通知（避免每次重复）
        if slots_avail != prev_slots:
            send_tg(
                f"🎉 CT8 注册队列有位置了！\n"
                f"剩余席位: {slots_avail}/{slots_total}\n"
                f"队列中: {queue}\n"
                f"已成功: {success}\n"
                f"🔗 {API_URL}"
            )

        # 注册未完成的邮箱
        pending = [e for e in EMAILS if e not in registered]
        if pending:
            for email in pending:
                log(f"📝 正在注册: {email}")
                result = None
                for attempt in range(MAX_RETRIES):
                    result = add_email(email)
                    if result and result.get("success"):
                        break
                    log(f"  ⚠ 第{attempt+1}次失败: {result.get('message', '')}")
                    time.sleep(3)

                if result and result.get("success"):
                    dup = result.get("duplicate", False)
                    status_text = "重复加入" if dup else "成功加入"
                    log(f"  ✅ {email} {status_text}")
                    registered.add(email)
                    send_tg(f"📧 {email} {status_text}注册队列{'（之前已加入过）' if dup else ''}")
                else:
                    err = result.get("message", "未知错误") if result else "请求失败"
                    log(f"  ❌ {email} 注册失败: {err}")
                    send_tg(f"❌ {email} 注册失败: {err}")

            save_json(REGISTERED_FILE, list(registered))
        else:
            log("📋 所有邮箱已注册过，等待下次补货")
    else:
        log("⏸️ 暂时没有可用位置")
        if slots_avail != prev_slots and prev_slots > 0:
            send_tg(f"⏸️ CT8 注册队列席位已用完（{slots_total} 席全满），等待补货")


if __name__ == "__main__":
    import sys, time
    main()
