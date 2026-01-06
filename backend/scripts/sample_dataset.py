import os
import json
import random
from pathlib import Path

OUT_PATH = Path("data") / "sampled_products.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def guess_dataset_root() -> Path:
    """
    Try common dataset root locations.
    Priority:
      1) env var FASHION200K_DIR
      2) repo_root/data/fashion200k
      3) repo_root/data
    We pick the first root that contains a 'labels' folder and at least one category folder.
    """
    repo_root = Path(__file__).resolve().parents[2]

    candidates = []
    env = os.getenv("FASHION200K_DIR")
    if env:
        candidates.append(Path(env))

    candidates += [
        repo_root / "data" / "fashion200k",
        repo_root / "data",
    ]

    for root in candidates:
        if not root.exists():
            continue
        labels = root / "labels"
        # your screenshot shows women/ at same level as labels/
        women = root / "women"
        if labels.exists() and women.exists():
            return root

        # sometimes categories are directly under root without "women"
        # check for any of these category folders
        for cat in ["dresses", "jackets", "pants", "skirts", "tops"]:
            if (root / cat).exists() and labels.exists():
                return root

    raise RuntimeError(
        "Could not locate dataset root. Set FASHION200K_DIR to the folder containing 'labels/' and 'women/' (or category dirs)."
    )

def load_label_map(labels_dir: Path) -> dict:
    """
    Build map: filename -> description (best effort).
    Accepts various label formats.
    """
    label_map = {}
    for txt in labels_dir.rglob("*.txt"):
        try:
            for line in txt.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                img_name = parts[0]
                desc = " ".join(parts[1:]).strip()
                if desc:
                    label_map[Path(img_name).name] = desc  # normalize to basename
        except Exception:
            continue
    return label_map

def iter_images(root: Path):
    """
    Walk common image folders:
      - root/women/**/*
      - root/**/ (if categories exist directly)
    """
    women_dir = root / "women"
    if women_dir.exists():
        search_root = women_dir
    else:
        search_root = root

    exts = (".jpg", ".jpeg", ".png", ".webp")
    for p in search_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            yield p

def main():
    root = guess_dataset_root()
    labels_dir = root / "labels"

    print(f"📦 Dataset root detected: {root}")

    label_map = load_label_map(labels_dir) if labels_dir.exists() else {}
    print(f"📝 Loaded {len(label_map)} label entries")

    imgs = list(iter_images(root))
    print(f"🖼️ Found {len(imgs)} images")

    if not imgs:
        raise RuntimeError("No images found under dataset root. Check folder structure.")

    N = int(os.getenv("SAMPLE_N", "1000"))
    SEED = int(os.getenv("SAMPLE_SEED", "42"))

    rnd = random.Random(SEED)
    rnd.shuffle(imgs)

    sampled = []
    seen = set()

    for img_path in imgs:
        pid = img_path.stem
        if pid in seen:
            continue
        seen.add(pid)

        # description: try label map, else folder-based fallback
        desc = label_map.get(img_path.name)
        if not desc:
            # build a simple deterministic description from folder names
            # e.g. women/dresses -> "women dresses"
            parts = [x for x in img_path.parts[-3:-1]]  # last 2 folders
            desc = " ".join(parts).replace("_", " ").strip() or img_path.parent.name

        sampled.append({
            "product_id": pid,
            "description": desc,
            "image_path": str(img_path.resolve())
        })

        if len(sampled) >= N:
            break

    OUT_PATH.write_text(json.dumps(sampled, indent=2), encoding="utf-8")
    print(f"✅ Sampled {len(sampled)} products")
    print(f"📄 Written: {OUT_PATH.resolve()}")

if __name__ == "__main__":
    main()
