"use client";

import { useState } from "react";

type ResultItem = {
  product_id: string;
  score: number;
  description?: string | null;
  image_path?: string | null;
};

export default function ProductCard({
  item,
  backendUrl,
}: {
  item: ResultItem;
  backendUrl: string;
}) {
  const [loaded, setLoaded] = useState(false);
  const [broken, setBroken] = useState(false);

  const img =
    item.image_path
      ? `${backendUrl}/api/image?path=${encodeURIComponent(item.image_path)}`
      : null;

  return (
    <article className="productCard">
      <div className="imageWrap">
        {!loaded && !broken ? <div className="imgSkeleton" /> : null}

        {img && !broken ? (
          <img
            className="productImg"
            src={img}
            alt={item.product_id}
            loading="lazy"
            style={{ opacity: loaded ? 1 : 0 }}
            onLoad={() => setLoaded(true)}
            onError={() => setBroken(true)}
          />
        ) : (
          <div className="imgPlaceholder">No Image</div>
        )}

        <div className="scoreBadge">{item.score.toFixed(2)}</div>
      </div>

      <div className="productBody">
        <div className="productId" title={String(item.product_id)}>
          {String(item.product_id)}
        </div>
        <div className="productDesc">
          {item.description ? item.description : <span className="muted">No description</span>}
        </div>

        {item.image_path ? (
          <div className="pathLine" title={item.image_path}>
            {item.image_path}
          </div>
        ) : null}
      </div>
    </article>
  );
}
