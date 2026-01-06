import os
import json
import random
from pathlib import Path

# Output file of sampled subset
OUT_PATH = Path("data") / "sampled_products.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def find_default_dataset_dir() -> Path:
    # Prefer env var; else assume repo_root/data/fashion200k
    env = os.getenv("FASHION200K_DIR")
    if env:
        return Path(env)
    # backend/ -> repo_root/
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "data" / "fashion200k"

def load_label_lines(labels_dir: Path) -> list[str]:
    """
    Fashion200k provides label files (train/test/val) with product/image + description-like text.
    Different sources format them differently; we robustly read all .txt under labels/.
    """
    if not labels_dir.exists():
        raise FileNotFoundError(f"labels dir not found: {labels_dir}")

    lines = []
    for p in labels_dir.rglob("*.txt"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            for ln in txt.splitlines():
                ln = ln.strip()
                if ln:
                    lines.append(ln)
        except Exception:
            continue
    if not lines:
        raise RuntimeError(f"No label lines found under: {labels_dir}")
    return lines

def parse_line_to_record(line: str, images_dir: Path) -> dict | None:
    """
    Robust parsing: many Fashion200k label formats include an image relative path
    and a text description separated by whitespace or tabs.
    We'll try best-effort extraction.

    We will:
    - find first token that looks like an image path (contains .jpg/.png)
    - remaining text becomes description
    """
    parts = line.split()
    img_idx = None
    for i, tok in enumerate(parts):
        t = tok.lower()
        if (".jpg" in t) or (".jpeg" in t) or (".png" in t):
            img_idx = i
            break
    if img_idx is None:
        return None

    img_rel = parts[img_idx]
    desc = " ".join(parts[img_idx + 1:]).strip()
    if not desc:
        return None

    img_path = images_dir / img_rel
    if not img_path.exists():
        # some datasets store images without nested dirs; try basename fallback
        alt = images_dir / Path(img_rel).name
        if alt.exists():
            img_path = alt
        else:
            return None

    # stable product id: use image path stem (or hash if needed)
    product_id = Path(img_rel).stem

    return {
        "product_id": product_id,
        "description": desc,
        "image_path": str(img_path.resolve())
    }

def main():
    dataset_dir = find_default_dataset_dir()
    labels_dir = dataset_dir / "labels"
    images_dir = dataset_dir / "images"

    N = int(os.getenv("SAMPLE_N", "1000"))
    SEED = int(os.getenv("SAMPLE_SEED", "42"))

    print(f"📦 Fashion200k dir: {dataset_dir}")
    print(f"🧪 Sampling N={N} SEED={SEED}")

    lines = load_label_lines(labels_dir)
    random.Random(SEED).shuffle(lines)

    sampled = []
    seen_desc = set()
    seen_pid = set()

    for ln in lines:
        rec = parse_line_to_record(ln, images_dir)
        if not rec:
            continue

        # diversity: keep unique descriptions + unique product ids
        d = rec["description"].lower()
        pid = rec["product_id"]
        if d in seen_desc or pid in seen_pid:
            continue

        seen_desc.add(d)
        seen_pid.add(pid)
        sampled.append(rec)

        if len(sampled) >= N:
            break

    if not sampled:
        raise RuntimeError("Could not sample any products. Check dataset paths/format.")

    OUT_PATH.write_text(json.dumps(sampled, indent=2), encoding="utf-8")
    print(f"✅ sampled {len(sampled)} products")
    print(f"📝 wrote: {OUT_PATH.resolve()}")

if __name__ == "__main__":
    main()
