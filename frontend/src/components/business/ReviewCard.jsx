import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Star, ThumbsUp, MessageCircle, Flag } from 'lucide-react';

/**
 * ReviewCard Component
 * 
 * Displays user reviews for vendors with:
 * - Star rating
 * - Review text
 * - Reviewer info (name, date)
 * - Photos
 * - Vendor reply
 * - Helpful votes
 * - Report functionality
 * 
 * @component
 * @example
 * <ReviewCard
 *   review={reviewData}
 *   onReply={handleVendorReply}
 *   onHelpful={handleMarkHelpful}
 * />
 */

export const ReviewCard = ({
  review = {},
  onReply,
  onHelpful,
  onReport,
  className,
}) => {
  const [isHelpful, setIsHelpful] = useState(review.isHelpfulMarked || false);
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyText, setReplyText] = useState('');

  // Default review data
  const reviewData = {
    id: review.id || '1',
    rating: review.rating || 5,
    text: review.text || 'Absolutely amazing service! The team was professional, punctual, and captured our special moments beautifully. Highly recommended!',
    reviewerName: review.reviewerName || 'Priya Sharma',
    reviewerImage: review.reviewerImage || 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop',
    reviewDate: review.reviewDate || '2 months ago',
    eventType: review.eventType || 'Wedding',
    eventDate: review.eventDate || 'Dec 15, 2023',
    images: review.images || [
      'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=300&h=300&fit=crop',
      'https://images.unsplash.com/photo-1505142468610-359e7d316be0?w=300&h=300&fit=crop',
    ],
    helpfulCount: review.helpfulCount || 42,
    vendorReply: review.vendorReply || {
      text: 'Thank you so much for the wonderful review! It was a pleasure working with you and your family. Best wishes!',
      date: '2 months ago',
      vendorName: 'Premium Photography Studio',
    },
  };

  const handleHelpful = () => {
    setIsHelpful(!isHelpful);
    onHelpful?.(reviewData.id, !isHelpful);
  };

  const handleReplySubmit = () => {
    if (replyText.trim()) {
      onReply?.(reviewData.id, replyText);
      setReplyText('');
      setShowReplyForm(false);
    }
  };

  // Star rating display
  const renderStars = (rating) => {
    return (
      <div className="flex gap-0.5">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            size={16}
            className={cn(
              'transition-colors',
              i < rating ? 'text-accent fill-accent' : 'text-border'
            )}
          />
        ))}
      </div>
    );
  };

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardContent className="p-lg space-y-lg">
        {/* Header with rating and date */}
        <div className="space-y-md">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <img
                src={reviewData.reviewerImage}
                alt={reviewData.reviewerName}
                className="w-10 h-10 rounded-full flex-shrink-0 object-cover"
              />
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-body-sm text-foreground line-clamp-1">
                  {reviewData.reviewerName}
                </p>
                <p className="text-tiny text-muted-foreground">
                  {reviewData.reviewDate}
                </p>
              </div>
            </div>
            <div className="text-right flex-shrink-0">
              {renderStars(reviewData.rating)}
            </div>
          </div>

          {/* Review metadata */}
          {(reviewData.eventType || reviewData.eventDate) && (
            <div className="flex flex-wrap gap-2">
              {reviewData.eventType && (
                <Badge variant="secondary" className="text-tiny">
                  {reviewData.eventType}
                </Badge>
              )}
              {reviewData.eventDate && (
                <span className="text-tiny text-muted-foreground">
                  Event: {reviewData.eventDate}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Review text */}
        <p className="text-body-md text-foreground leading-relaxed">
          {reviewData.text}
        </p>

        {/* Review images */}
        {reviewData.images && reviewData.images.length > 0 && (
          <div className="flex gap-2 overflow-x-auto -mx-lg px-lg py-sm">
            {reviewData.images.map((image, idx) => (
              <div
                key={idx}
                className="w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden bg-muted cursor-pointer hover:opacity-80 transition-opacity"
              >
                <img
                  src={image}
                  alt={`Review image ${idx + 1}`}
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        )}

        {/* Vendor reply */}
        {reviewData.vendorReply && (
          <div className="bg-primary/5 border border-primary/10 rounded-lg p-md space-y-md">
            <p className="text-tiny font-semibold text-primary uppercase">
              Vendor Response
            </p>
            <p className="text-body-sm text-foreground">
              {reviewData.vendorReply.text}
            </p>
            <p className="text-tiny text-muted-foreground">
              {reviewData.vendorReply.vendorName} • {reviewData.vendorReply.date}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-md border-t border-border">
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleHelpful}
              className={cn(
                'gap-1',
                isHelpful && 'bg-primary/10 text-primary'
              )}
            >
              <ThumbsUp size={16} />
              {isHelpful ? 'Helpful' : 'Helpful'} ({reviewData.helpfulCount})
            </Button>
            {!reviewData.vendorReply && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowReplyForm(!showReplyForm)}
                className="gap-1"
              >
                <MessageCircle size={16} />
                Reply
              </Button>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onReport?.(reviewData.id)}
            className="text-error hover:bg-error/5 gap-1"
          >
            <Flag size={16} />
            Report
          </Button>
        </div>

        {/* Reply form */}
        {showReplyForm && (
          <div className="space-y-md pt-md border-t border-border">
            <textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Share your response..."
              className="w-full h-20 px-3 py-2 border border-input rounded-lg text-body-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
            />
            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowReplyForm(false);
                  setReplyText('');
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                disabled={!replyText.trim()}
                onClick={handleReplySubmit}
              >
                Post Reply
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * ReviewsList Component
 * Container for multiple reviews with filters
 */
export const ReviewsList = ({
  reviews = [],
  onReply,
  onHelpful,
  onReport,
  className,
}) => {
  const [filterRating, setFilterRating] = useState(null);
  const [sortBy, setSortBy] = useState('recent');

  const filteredReviews = filterRating
    ? reviews.filter((r) => r.rating === filterRating)
    : reviews;

  const sortedReviews = [...filteredReviews].sort((a, b) => {
    if (sortBy === 'helpful') {
      return b.helpfulCount - a.helpfulCount;
    }
    // 'recent' is default order
    return 0;
  });

  return (
    <div className={cn('space-y-lg', className)}>
      {/* Filters */}
      <div className="space-y-md">
        <h3 className="text-h5 font-heading">Reviews ({reviews.length})</h3>
        
        <div className="flex flex-wrap gap-2">
          <Button
            variant={filterRating === null ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setFilterRating(null)}
          >
            All
          </Button>
          {[5, 4, 3, 2, 1].map((rating) => {
            const count = reviews.filter((r) => r.rating === rating).length;
            return (
              <Button
                key={rating}
                variant={filterRating === rating ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setFilterRating(rating)}
                className="gap-1"
              >
                <Star size={14} className="fill-accent text-accent" />
                {rating} ({count})
              </Button>
            );
          })}
        </div>

        {/* Sort */}
        <div className="flex gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 text-body-sm border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="recent">Most Recent</option>
            <option value="helpful">Most Helpful</option>
            <option value="rating-high">Highest Rating</option>
            <option value="rating-low">Lowest Rating</option>
          </select>
        </div>
      </div>

      {/* Reviews */}
      <div className="space-y-lg">
        {sortedReviews.length > 0 ? (
          sortedReviews.map((review) => (
            <ReviewCard
              key={review.id}
              review={review}
              onReply={onReply}
              onHelpful={onHelpful}
              onReport={onReport}
            />
          ))
        ) : (
          <div className="text-center py-12">
            <p className="text-muted-foreground text-body-md">
              No reviews yet. Be the first to share your experience!
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewCard;
