import React from 'react';
import './ProductCard.css';

interface ProductCardProps {
    imageUrl?: string;
    partNumber: string;
    name: string;
    price?: number;
    onCheckCompatibility: (partNumber: string) => void;
}

const ProductCard: React.FC<ProductCardProps> = ({
    imageUrl,
    partNumber,
    name,
    price,
    onCheckCompatibility
}) => {
    const handleCheckCompatibility = () => {
        onCheckCompatibility(partNumber);
    };

    const defaultImageUrl = 'https://via.placeholder.com/150?text=No+Image';

    return (
        <div className="product-card">
            <div className="product-image-container">
                <img
                    src={imageUrl || defaultImageUrl}
                    alt={name}
                    className="product-image"
                    onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = defaultImageUrl;
                    }}
                />
            </div>
            <div className="product-info">
                <h3 className="product-name">{name}</h3>
                <p className="product-part-number">Part #: {partNumber}</p>
                {price !== undefined && (
                    <p className="product-price">${price.toFixed(2)}</p>
                )}
                <button
                    className="compatibility-button"
                    onClick={handleCheckCompatibility}
                >
                    Check Compatibility
                </button>
            </div>
        </div>
    );
};

export default ProductCard; 