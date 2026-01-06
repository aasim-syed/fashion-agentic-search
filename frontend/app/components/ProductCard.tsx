import React from 'react';

type Props = {
    product: {
      product_id: string;
      description: string;
      image: string;
      score: number;
    };
  };
  
  export default function ProductCard({ product }: Props) {
    return (
      <div className="bg-white/5 backdrop-blur border border-white/10 rounded-xl overflow-hidden hover:scale-[1.02] transition">
        <img
          src={`http://localhost:8000/${product.image}`}
          alt={product.description}
          className="w-full h-48 object-cover"
        />
  
        <div className="p-3 space-y-1">
          <p className="text-sm text-zinc-300">{product.description}</p>
          <div className="flex justify-between text-xs text-zinc-500">
            <span>ID: {product.product_id}</span>
            <span>Score: {product.score.toFixed(2)}</span>
          </div>
        </div>
      </div>
    );
  }
  