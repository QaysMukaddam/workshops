// useState tracks whether THIS user has liked the notice (see the note
// below about why this starts as false every page load).
import { useState } from 'react';

// Link makes the whole card clickable, navigating to the notice's detail page.
import { Link } from 'react-router-dom';

import { likeNotice, unlikeNotice } from '../api/api';
import { useAuth } from '../context/AuthContext';
import Card from './Card';

// Displays one notice in the list: name, message, date, view count, and
// a like button. Receives the notice object as a prop.
export default function NoticeCard({ notice }) {
  // Need the token to make authenticated like/unlike requests.
  const { token } = useAuth();

  // Local copy of the like count, so clicking Like updates instantly
  // without waiting for a full page refetch.
  const [likeCount, setLikeCount] = useState(notice.like_count);

  // NOTE: the backend's GET /notices doesn't currently say whether THIS
  // user already liked a notice, only the total count — so this starts
  // false on every page load, even if you'd liked it in a past session.
  // Clicking still works correctly within the current session.
  const [liked, setLiked] = useState(false);

  // Handles clicking the like button.
  async function handleLikeClick(e) {
    // Stop the click from also triggering the surrounding <Link>'s
    // navigation to the detail page.
    e.preventDefault();
    e.stopPropagation();

    try {
      if (liked) {
        // Already liked — this click means "unlike".
        await unlikeNotice(notice.id, token);
        setLikeCount((count) => count - 1);
        setLiked(false);
      } else {
        // Not liked yet — this click means "like".
        await likeNotice(notice.id, token);
        setLikeCount((count) => count + 1);
        setLiked(true);
      }
    } catch (err) {
      // Log rather than crash the page if the request fails.
      console.error(err.message);
    }
  }

  return (
    // The whole card is a link to the notice's detail page.
    <Link to={`/notices/${notice.id}`}>
      <Card className="hover:border-accent/40 transition-colors cursor-pointer text-left">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-white">{notice.name}</h2>
          {/* Formats the ISO timestamp into a readable date. */}
          <span className="text-xs text-gray-500">{new Date(notice.created_at).toLocaleDateString()}</span>
        </div>

        <p className="text-gray-300 mb-4">{notice.message}</p>

        <div className="flex items-center gap-4 text-sm text-gray-400">
          <span>👁 {notice.view_count} views</span>
          {/* Color changes to the accent color once liked, giving clear
              visual feedback. */}
          <button onClick={handleLikeClick} className={`flex items-center gap-1 ${liked ? 'text-accent' : 'text-gray-400'} hover:text-accent transition-colors`}>
            ❤ {likeCount}
          </button>
        </div>
      </Card>
    </Link>
  );
}