/**
 * Community store for managing feed, likes, comments, and follows
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getFeed,
  getGenerationDetail,
  toggleLike as toggleLikeApi,
  getComments,
  addComment as addCommentApi,
  deleteComment as deleteCommentApi,
  toggleFollow as toggleFollowApi,
} from '@/services/community.service'

export const useCommunityStore = defineStore('community', () => {
  // State
  const feed = ref([])
  const currentGeneration = ref(null)
  const comments = ref([])
  const currentPage = ref(1)
  const hasMore = ref(true)
  const loading = ref(false)
  const error = ref(null)

  // Actions
  async function fetchFeed(page = 1, append = false) {
    loading.value = true
    error.value = null

    try {
      const data = await getFeed({ page })

      if (append) {
        feed.value = [...feed.value, ...(data.results || [])]
      } else {
        feed.value = data.results || []
      }

      currentPage.value = page
      hasMore.value = !!data.next

      return data
    } catch (err) {
      console.warn('Failed to fetch feed from API, using mock data:', err)

      // Mock data for development
      const mockData = [
        {
          id: 1,
          result_url: 'https://picsum.photos/400/600',
          description: 'Beautiful sunset painting in Van Gogh style',
          user: {
            id: 1,
            username: 'Vincent',
            avatar: null,
          },
          style: {
            id: 1,
            name: 'Van Gogh Style',
            artist_id: 1,
          },
          like_count: 120,
          comment_count: 15,
          is_liked_by_current_user: false,
          is_bookmarked: false,
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: 2,
          result_url: 'https://picsum.photos/400/500',
          description: 'Abstract modern art with vibrant colors',
          user: {
            id: 2,
            username: 'ArtLover',
            avatar: null,
          },
          style: {
            id: 2,
            name: 'Abstract Modern',
            artist_id: 2,
          },
          like_count: 85,
          comment_count: 8,
          is_liked_by_current_user: true,
          is_bookmarked: false,
          created_at: new Date(Date.now() - 7200000).toISOString(),
        },
        {
          id: 3,
          result_url: 'https://picsum.photos/400/700',
          description: 'Landscape with impressionist touches',
          user: {
            id: 1,
            username: 'Vincent',
            avatar: null,
          },
          style: {
            id: 3,
            name: 'Impressionist',
            artist_id: 1,
          },
          like_count: 200,
          comment_count: 25,
          is_liked_by_current_user: false,
          is_bookmarked: true,
          created_at: new Date(Date.now() - 10800000).toISOString(),
        },
        {
          id: 4,
          result_url: 'https://picsum.photos/400/450',
          description: 'Minimalist geometric composition',
          user: {
            id: 3,
            username: 'ModernArtist',
            avatar: null,
          },
          style: {
            id: 4,
            name: 'Minimalist',
            artist_id: 3,
          },
          like_count: 95,
          comment_count: 12,
          is_liked_by_current_user: false,
          is_bookmarked: false,
          created_at: new Date(Date.now() - 14400000).toISOString(),
        },
      ]

      if (append) {
        feed.value = [...feed.value, ...mockData]
      } else {
        feed.value = mockData
      }

      currentPage.value = page
      hasMore.value = page < 2 // Only 2 pages of mock data

      return {
        results: mockData,
        next: page < 2 ? true : null,
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchNextPage() {
    if (!hasMore.value || loading.value) return

    return fetchFeed(currentPage.value + 1, true)
  }

  async function fetchGenerationDetail(generationId) {
    loading.value = true
    error.value = null

    try {
      const data = await getGenerationDetail(generationId)
      currentGeneration.value = data
      return data
    } catch (err) {
      error.value = err.message || 'Failed to fetch generation detail'
      console.error('Failed to fetch generation detail:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function toggleLike(generationId) {
    try {
      const data = await toggleLikeApi(generationId)

      // Update feed item if exists
      const feedItem = feed.value.find((item) => item.id === generationId)
      if (feedItem) {
        feedItem.is_liked_by_current_user = data.is_liked
        feedItem.like_count = data.like_count
      }

      // Update current generation if it's the same
      if (currentGeneration.value && currentGeneration.value.id === generationId) {
        currentGeneration.value.is_liked_by_current_user = data.is_liked
        currentGeneration.value.like_count = data.like_count
      }

      return data
    } catch (err) {
      console.error('Failed to toggle like:', err)
      throw err
    }
  }

  async function fetchComments(generationId, page = 1) {
    loading.value = true
    error.value = null

    try {
      const data = await getComments(generationId, { page })
      comments.value = data.results || []
      return data
    } catch (err) {
      error.value = err.message || 'Failed to fetch comments'
      console.error('Failed to fetch comments:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function addComment(generationId, content, parentId = null) {
    try {
      const comment = await addCommentApi(generationId, content, parentId)

      // Add to comments list
      comments.value.unshift(comment)

      // Update comment count in feed
      const feedItem = feed.value.find((item) => item.id === generationId)
      if (feedItem && !parentId) {
        // Only increment for top-level comments
        feedItem.comment_count += 1
      }

      // Update current generation
      if (currentGeneration.value && currentGeneration.value.id === generationId && !parentId) {
        currentGeneration.value.comment_count += 1
      }

      return comment
    } catch (err) {
      console.error('Failed to add comment:', err)
      throw err
    }
  }

  async function deleteComment(commentId, generationId) {
    try {
      await deleteCommentApi(commentId)

      // Remove from comments list
      const index = comments.value.findIndex((c) => c.id === commentId)
      if (index !== -1) {
        const isTopLevel = !comments.value[index].parent
        comments.value.splice(index, 1)

        // Update comment count
        const feedItem = feed.value.find((item) => item.id === generationId)
        if (feedItem && isTopLevel) {
          feedItem.comment_count = Math.max(0, feedItem.comment_count - 1)
        }

        if (currentGeneration.value && currentGeneration.value.id === generationId && isTopLevel) {
          currentGeneration.value.comment_count = Math.max(0, currentGeneration.value.comment_count - 1)
        }
      }
    } catch (err) {
      console.error('Failed to delete comment:', err)
      throw err
    }
  }

  async function toggleFollow(userId) {
    try {
      const data = await toggleFollowApi(userId)
      return data
    } catch (err) {
      console.error('Failed to toggle follow:', err)
      throw err
    }
  }

  function clearFeed() {
    feed.value = []
    currentPage.value = 1
    hasMore.value = true
    error.value = null
  }

  function clearCurrentGeneration() {
    currentGeneration.value = null
    comments.value = []
  }

  return {
    // State
    feed,
    currentGeneration,
    comments,
    currentPage,
    hasMore,
    loading,
    error,
    // Actions
    fetchFeed,
    fetchNextPage,
    fetchGenerationDetail,
    toggleLike,
    fetchComments,
    addComment,
    deleteComment,
    toggleFollow,
    clearFeed,
    clearCurrentGeneration,
  }
})
