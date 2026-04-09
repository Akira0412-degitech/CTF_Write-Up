# Git Workflow Rules for Claude Code

## ⚡ 作業開始時（必ず最初に実行）
1. `git fetch origin`
2. `git checkout main`
3. `git reset --hard origin/main`  # 常にoriginと完全一致させる
4. ブランチ作成: `git checkout -b claude/[作業内容]-$(date +%Y%m%d)`

> **⚠️ Worktree環境の場合:**
> `git checkout main` は親ディレクトリがすでに `main` を使用しているためエラーになる。
> 代わりに以下で origin/main に追いつく:
> ```bash
> git fetch origin
> git rebase origin/main
> git checkout -b claude/[作業内容]-$(date +%Y%m%d)
> ```
> mainの最新化（作業終了時）も `git checkout main` の代わりに親ディレクトリで `git pull origin main` を実行する。

## ✅ 作業終了時（必ず実行）
1. `git add -A`
2. `git commit -m "[prefix]: [変更内容の説明]"`
3. `git push origin [ブランチ名]`
4. PRを作成して即マージ:
```bash
gh pr create \
  --title "[作業内容]" \
  --body "## 変更内容\n[説明]\n\n## 確認済み\n- [ ] 動作確認" \
  --base main

gh pr merge --merge --delete-branch
```
5. ローカルのmainを最新化:
```bash
git checkout main
git pull origin main
```

## 🏷️ ブランチ命名規則
- `claude/feature-xxx-YYYYMMDD`  # 新機能
- `claude/fix-xxx-YYYYMMDD`      # バグ修正
- `claude/refactor-xxx-YYYYMMDD` # リファクタ
- `claude/docs-xxx-YYYYMMDD`     # ドキュメント

## 📝 コミットプレフィックス
- `feat:` 新機能
- `fix:` バグ修正
- `refactor:` リファクタリング
- `docs:` ドキュメント
- `chore:` 設定・雑務

## ⚠️ 禁止事項
- mainブランチへの直接コミット
- `git push --force` (originとずれた場合はreset --hardで解決)
- conflict状態でのPR作成
