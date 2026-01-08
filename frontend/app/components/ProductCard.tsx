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
  const img = item.image_path
    ? `${backendUrl}/api/image?path=${encodeURIComponent(item.image_path)}`
    : null;

  const [imgLoading, setImgLoading] = useState(!!img);
  const [imgOk, setImgOk] = useState(!!img);

  return (
    <article className="productCard">
      <div className="imageWrap">
        {img && imgOk ? (
          <>
            <img
              className="productImg"
              src={img}
              alt={item.product_id}
              loading="lazy"
              onLoad={() => setImgLoading(false)}
              onError={() => {
                setImgOk(false);
                setImgLoading(false);
              }}
            />
            {imgLoading ? <div className="imgSkeleton" /> : null}
          </>
        ) : (
          <div className="imgPlaceholder">No Image</div>
        )}

        <div className="scoreBadge">{item.score.toFixed(2)}</div>
      </div>

      <div className="productBody">
        <div className="productId" title={item.product_id}>
          {item.product_id}
        </div>

        <div className="productDesc">
          {item.description ? (
            item.description
          ) : (
            <span className="muted">No description</span>
          )}
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
