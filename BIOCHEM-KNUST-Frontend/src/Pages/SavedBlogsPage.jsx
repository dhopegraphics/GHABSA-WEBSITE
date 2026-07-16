import React, { useCallback, useContext, useEffect, useState } from 'react';
import { BookMarked } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useSavedBlogs } from '../Context/SavedBlogsContext';
import { scrollToTop } from '../utils/scrollToTop';
import { BACKEND_HOST } from '../utils/config';
import { UserContext } from '../Context/UserContext';
import useAxiosWithRefresh from '../Hooks/useAxiosWithRefresh';

export function SavedBlogsPage() {
  const { savedBlogs, setSavedBlogs } = useSavedBlogs();
  const { user } = useContext(UserContext);

  const axiosInstance = useAxiosWithRefresh();
  const [isLoading, setIsLoading] = useState(true);

  const fetchSaved = useCallback(async () => {
    if (user?.access) {
      try {
        setIsLoading(true);
        const response = await axiosInstance.get(
          `${BACKEND_HOST}/accounts/saved-blogs/`,
          {
            headers: { Authorization: `Bearer ${user.access}` },
          }
        );
        setSavedBlogs(response.data?.data?.blogs || []);
      } catch (error) {
        console.error('Failed to fetch saved blogs:', error);
      } finally {
        setIsLoading(false);
      }
    }
  }, [user, axiosInstance, setSavedBlogs]);

  useEffect(() => {
    scrollToTop();
    fetchSaved();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 px-4 md:px-8 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-extrabold text-gray-900 mb-4">Saved Blogs</h1>

        {isLoading && savedBlogs ? (
          <div className="grid gap-6">
          {savedBlogs?.map((blog) => (
            <Link
              key={blog?.news_id}
              to={`/blog/${blog?.news_id}`}
              state={{ blog, saved: true }}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6 flex items-start gap-4"
              aria-label={`View details of ${blog?.title}`}
            >
              <div className="p-4 bg-blue-50 rounded-lg flex items-center justify-center">
                <BookMarked className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">
                  {blog?.title}
                </h3>
                <p className="text-gray-600 mt-2 line-clamp-1">
                  {blog?.report}
                </p>
                <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
                  <span>
                    {new Date(blog?.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </span>
                  <span>{blog?.minutes_read} minutes read</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
        )
        : isLoading ? (
          <div className="grid gap-6">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div
                key={idx}
                className="bg-white rounded-lg shadow p-6 flex items-start gap-4 animate-pulse"
              >
                <div className="p-4 bg-gray-200 rounded-lg h-12 w-12"></div>
                <div className="flex-1 space-y-4">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                </div>
              </div>
            ))}
          </div>
        ) : savedBlogs?.length === 0 || !savedBlogs ? (
          <div className="text-center mt-16">
            <p className="text-gray-600 text-2xl font-bold">You have no saved blogs yet.</p>
            <p className="text-gray-500 mt-2">
              Explore interesting <Link to={'/blogs?page=1'} className='underline'>blogs</Link> and save them to read later.
            </p>
          </div>
        ) : (
          <div className="grid gap-6">
            {savedBlogs?.map((blog) => (
              <Link
                key={blog?.news_id}
                to={`/blog/${blog?.news_id}`}
                state={{ blog, saved: true }}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6 flex items-start gap-4"
                aria-label={`View details of ${blog?.title}`}
              >
                <div className="p-4 bg-blue-50 rounded-lg flex items-center justify-center">
                  <BookMarked className="w-6 h-6 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">
                    {blog?.title}
                  </h3>
                  <p className="text-gray-600 mt-2 line-clamp-1">
                    {blog?.report}
                  </p>
                  <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
                    <span>
                      {new Date(blog?.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </span>
                    <span>{blog?.minutes_read} minutes read</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
