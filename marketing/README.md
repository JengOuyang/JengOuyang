# marketing/ — 行銷產出

| 子目錄 | 內容 |
|---|---|
| `queue/<date>/<content_id>/` | CREATIVE 的待發佈草稿：`image_*.jpg`、`caption.txt`、`alt.txt`、`meta.json` |
| `longform/` | 部落格／電子報版本 |
| `analytics/<week>.md` | GROWTH 的週報 |
| `assets/` | 品牌素材：logo、字體、Canva 模板 ID 對照 |

發佈流程：CREATIVE 產草稿 → `#marketing-review` 預覽 → 你 `!publish <content_id>` → `scripts/publisher.py` 經 Meta Graph API 發佈。**LLM 永遠碰不到 Meta token。**
