<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50"
        @click.self="close"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black bg-opacity-60 transition-opacity" @click="close"></div>

        <!-- Modal Content - Bottom Sheet Style -->
        <div class="fixed bottom-0 left-0 right-0 flex flex-col" style="height: 65vh">
          <div
            class="bg-white rounded-t-3xl shadow-xl max-w-screen-sm mx-auto w-full flex flex-col h-full"
            @click.stop
          >
            <!-- Drag Handle -->
            <div class="flex justify-center pt-3 pb-2">
              <div class="w-10 h-1 bg-gray-300 rounded-full"></div>
            </div>

            <!-- Header -->
            <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200">
              <div class="w-6"></div>
              <h3 class="text-base font-semibold text-gray-900">
                Comments
              </h3>
              <button
                @click="close"
                class="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>

            <!-- Comments List -->
            <div class="flex-1 overflow-y-auto p-4 space-y-4">
              <!-- Loading State -->
              <div v-if="loading" class="text-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              </div>

              <!-- Empty State -->
              <div v-else-if="comments.length === 0" class="text-center py-8">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p class="mt-2 text-sm text-gray-600">{{ $t('comments.empty') }}</p>
              </div>

              <!-- Comment Items -->
              <div
                v-else
                v-for="comment in comments"
                :key="comment.id"
                class="flex space-x-3"
              >
                <!-- Avatar -->
                <img
                  :src="comment.user.avatar || '/default-avatar.png'"
                  :alt="comment.user.username"
                  class="w-9 h-9 rounded-full object-cover flex-shrink-0"
                />

                <!-- Comment Content -->
                <div class="flex-1 min-w-0">
                  <!-- Username and Time -->
                  <div class="flex items-center space-x-2 mb-1">
                    <span class="font-semibold text-sm text-gray-900">
                      {{ comment.user.username }}
                    </span>
                    <span class="text-xs text-gray-500">
                      {{ formatTime(comment.created_at) }}
                    </span>
                  </div>

                  <!-- Comment Text -->
                  <p class="text-sm text-gray-900 break-words mb-2">
                    {{ comment.content }}
                  </p>

                  <!-- Actions -->
                  <div class="flex items-center space-x-4 text-xs text-gray-500">
                    <button
                      @click="handleLikeComment(comment.id)"
                      class="font-semibold hover:text-gray-700"
                    >
                      {{ comment.like_count || 0 }} {{ comment.like_count === 1 ? 'like' : 'likes' }}
                    </button>
                    <button class="font-semibold hover:text-gray-700">
                      Reply
                    </button>
                    <button
                      v-if="canDelete(comment)"
                      @click="handleDelete(comment.id)"
                      class="font-semibold text-red-600 hover:text-red-700"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                <!-- Like Button -->
                <button
                  @click="handleLikeComment(comment.id)"
                  class="flex-shrink-0 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <svg
                    class="w-5 h-5"
                    :fill="comment.is_liked ? 'currentColor' : 'none'"
                    :class="comment.is_liked ? 'text-red-500' : ''"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                    />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Comment Input -->
            <div class="border-t border-gray-200 p-3 bg-white">
              <form @submit.prevent="handleSubmit" class="flex items-center space-x-3">
                <!-- User Avatar -->
                <img
                  :src="authStore.user?.avatar || '/default-avatar.png'"
                  :alt="authStore.user?.username || 'You'"
                  class="w-8 h-8 rounded-full object-cover flex-shrink-0"
                />

                <!-- Input Field -->
                <input
                  v-model="newComment"
                  type="text"
                  placeholder="Add a comment..."
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-full focus:outline-none focus:border-gray-400 text-sm"
                  :disabled="submitting"
                />

                <!-- Post Button -->
                <button
                  type="submit"
                  :disabled="!newComment.trim() || submitting"
                  class="text-blue-500 font-semibold text-sm disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  {{ submitting ? 'Posting...' : 'Post' }}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  imageId: {
    type: [String, Number],
    required: true,
  },
})

const emit = defineEmits(['close', 'comment-added', 'comment-deleted'])

const authStore = useAuthStore()

// State
const comments = ref([])
const newComment = ref('')
const loading = ref(false)
const submitting = ref(false)

// Watch for modal open/close
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen) {
    await fetchComments()
  } else {
    newComment.value = ''
  }
})

// Methods
async function fetchComments() {
  loading.value = true
  try {
    // TODO: Replace with actual API call
    // const response = await getImageComments(props.imageId)
    // comments.value = response.data

    // Mock data for now
    comments.value = [
      {
        id: 1,
        user: {
          id: 1,
          username: 'artist_user',
          avatar: null,
        },
        content: '정말 멋진 작품이네요!',
        like_count: 1,
        is_liked: false,
        created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
      },
      {
        id: 2,
        user: {
          id: 2,
          username: 'art_lover',
          avatar: null,
        },
        content: '색감이 정말 환상적입니다 👏',
        like_count: 10,
        is_liked: false,
        created_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
      },
    ]
  } catch (error) {
    console.error('Failed to fetch comments:', error)
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!newComment.value.trim()) return

  submitting.value = true
  try {
    // TODO: Replace with actual API call
    // await createComment(props.imageId, { content: newComment.value })

    // Mock: Add comment locally
    const mockComment = {
      id: Date.now(),
      user: {
        id: authStore.user?.id || 0,
        username: authStore.user?.username || 'You',
        avatar: authStore.user?.avatar || null,
      },
      content: newComment.value,
      created_at: new Date().toISOString(),
    }
    comments.value.push(mockComment)

    newComment.value = ''
    emit('comment-added', mockComment)
  } catch (error) {
    console.error('Failed to post comment:', error)
  } finally {
    submitting.value = false
  }
}

async function handleDelete(commentId) {
  if (!confirm('정말 삭제하시겠습니까?')) return

  try {
    // TODO: Replace with actual API call
    // await deleteComment(commentId)

    comments.value = comments.value.filter(c => c.id !== commentId)
    emit('comment-deleted', commentId)
  } catch (error) {
    console.error('Failed to delete comment:', error)
  }
}

async function handleLikeComment(commentId) {
  try {
    // TODO: Replace with actual API call
    // await toggleCommentLike(commentId)

    // Mock: Toggle like locally
    const comment = comments.value.find(c => c.id === commentId)
    if (comment) {
      comment.is_liked = !comment.is_liked
      comment.like_count += comment.is_liked ? 1 : -1
    }
  } catch (error) {
    console.error('Failed to like comment:', error)
  }
}

function canDelete(comment) {
  return authStore.user && comment.user.id === authStore.user.id
}

function close() {
  emit('close')
}

function formatTime(timestamp) {
  const now = new Date()
  const commentTime = new Date(timestamp)
  const diffInSeconds = Math.floor((now - commentTime) / 1000)

  if (diffInSeconds < 60) {
    return '방금 전'
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return `${minutes}분 전`
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return `${hours}시간 전`
  } else if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400)
    return `${days}일 전`
  } else {
    return commentTime.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
    })
  }
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.95);
}
</style>
