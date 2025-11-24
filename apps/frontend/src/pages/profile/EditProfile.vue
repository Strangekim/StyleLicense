<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
        <button
          @click="handleCancel"
          class="text-gray-700 hover:text-gray-900 font-medium"
        >
          {{ $t('editProfile.cancel') }}
        </button>
        <h1 class="text-lg font-semibold text-gray-900">{{ $t('editProfile.title') }}</h1>
        <button
          @click="handleSave"
          :disabled="saving"
          class="text-blue-600 hover:text-blue-700 font-semibold disabled:opacity-50"
        >
          {{ saving ? $t('editProfile.saving') : $t('editProfile.done') }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Edit Form -->
    <div v-else class="max-w-2xl mx-auto px-4 py-6">
      <!-- Profile Photo Section -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div class="flex flex-col items-center">
          <!-- Avatar -->
          <div class="relative mb-4">
            <div class="w-24 h-24 rounded-full overflow-hidden bg-gray-200 border-4 border-white shadow-md">
              <img
                v-if="form.avatar || previewAvatar"
                :src="previewAvatar || form.avatar"
                alt="Profile photo"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center bg-blue-100 text-blue-600 text-3xl font-semibold">
                {{ form.username.charAt(0).toUpperCase() }}
              </div>
            </div>
          </div>

          <!-- Change Photo Button -->
          <label class="text-blue-600 hover:text-blue-700 font-medium cursor-pointer">
            {{ $t('editProfile.changeProfilePhoto') }}
            <input
              type="file"
              accept="image/*"
              @change="handlePhotoChange"
              class="hidden"
            />
          </label>
        </div>
      </div>

      <!-- Profile Information -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <!-- Username -->
        <div class="mb-4">
          <label for="username" class="block text-sm font-medium text-gray-700 mb-2">
            {{ $t('editProfile.username') }}
          </label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :placeholder="$t('editProfile.usernamePlaceholder')"
          />
        </div>

        <!-- Bio -->
        <div class="mb-4">
          <label for="bio" class="block text-sm font-medium text-gray-700 mb-2">
            {{ $t('editProfile.bio') }}
          </label>
          <textarea
            id="bio"
            v-model="form.bio"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            :placeholder="$t('editProfile.bioPlaceholder')"
          ></textarea>
          <p class="mt-1 text-xs text-gray-500">
            {{ form.bio.length }}/150 {{ $t('editProfile.characters') }}
          </p>
        </div>

        <!-- Switch to Professional Account -->
        <button
          v-if="!isProfessional"
          @click="handleSwitchToProfessional"
          class="text-blue-600 hover:text-blue-700 font-medium text-sm"
        >
          {{ $t('editProfile.switchToProfessional') }}
        </button>
      </div>

      <!-- Private Information -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">{{ $t('editProfile.privateInformation') }}</h2>

        <!-- Email -->
        <div class="mb-4">
          <label for="email" class="block text-sm font-medium text-gray-700 mb-2">
            {{ $t('editProfile.email') }}
          </label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :placeholder="$t('editProfile.emailPlaceholder')"
            disabled
          />
          <p class="mt-1 text-xs text-gray-500">
            {{ $t('editProfile.emailCannotBeChanged') }}
          </p>
        </div>

        <!-- Signature -->
        <div class="mb-4">
          <label for="signature" class="block text-sm font-medium text-gray-700 mb-2">
            {{ $t('editProfile.signature') }}
          </label>

          <!-- Signature Display -->
          <div v-if="form.signature || previewSignature" class="mb-2 p-4 border border-gray-300 rounded-lg bg-gray-50">
            <img
              v-if="previewSignature || (form.signature && form.signature.startsWith('http'))"
              :src="previewSignature || form.signature"
              alt="Signature"
              class="max-h-20 object-contain"
            />
            <p v-else class="text-gray-700 font-signature text-2xl">
              {{ form.signature }}
            </p>
          </div>

          <!-- Signature Input Options -->
          <div class="flex gap-2">
            <input
              id="signature"
              v-model="form.signature"
              type="text"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="$t('editProfile.signaturePlaceholder')"
            />
            <label class="px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-200 cursor-pointer flex items-center">
              <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {{ $t('editProfile.upload') }}
              <input
                type="file"
                accept="image/*"
                @change="handleSignatureChange"
                class="hidden"
              />
            </label>
          </div>
        </div>
      </div>

      <!-- Danger Zone -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6 border-l-4 border-red-500">
        <h2 class="text-lg font-semibold text-red-600 mb-4">{{ $t('editProfile.dangerZone') }}</h2>
        <button
          @click="handleDeleteAccount"
          class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          {{ $t('editProfile.deleteAccount') }}
        </button>
        <p class="mt-2 text-xs text-gray-600">
          {{ $t('editProfile.deleteAccountWarning') }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

// State
const loading = ref(false)
const saving = ref(false)
const isProfessional = ref(false)
const previewAvatar = ref(null)
const previewSignature = ref(null)

const form = ref({
  username: '',
  bio: '',
  email: '',
  avatar: null,
  signature: '',
})

// Methods
onMounted(async () => {
  await loadProfile()
})

async function loadProfile() {
  loading.value = true
  try {
    // TODO: Replace with actual API call
    // const response = await getUserProfile()
    // form.value = response.data

    // Mock data from auth store
    form.value = {
      username: authStore.user?.username || 'jacob_w',
      bio: authStore.user?.bio || 'Everything is designed.',
      email: authStore.user?.email || 'jacob.west@gmail.com',
      avatar: authStore.user?.avatar || null,
      signature: 'Vincent',
    }

    // Check if user is professional
    isProfessional.value = authStore.user?.role === 'artist'
  } catch (error) {
    console.error('Failed to load profile:', error)
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (saving.value) return

  // Validate form
  if (!form.value.username.trim()) {
    alert(t('editProfile.errors.usernameRequired'))
    return
  }

  if (form.value.bio.length > 150) {
    alert(t('editProfile.errors.bioTooLong'))
    return
  }

  saving.value = true
  try {
    // TODO: Replace with actual API call
    // const formData = new FormData()
    // if (previewAvatar.value) {
    //   formData.append('avatar', avatarFile)
    // }
    // if (previewSignature.value) {
    //   formData.append('signature', signatureFile)
    // }
    // formData.append('username', form.value.username)
    // formData.append('bio', form.value.bio)
    // await updateUserProfile(formData)

    // Mock: Update auth store
    if (authStore.user) {
      authStore.user.username = form.value.username
      authStore.user.avatar = previewAvatar.value || form.value.avatar
    }

    // Navigate back to profile
    router.push('/profile')
  } catch (error) {
    console.error('Failed to save profile:', error)
    alert(t('editProfile.errors.saveFailed'))
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  // Check if there are unsaved changes
  const hasChanges =
    form.value.username !== authStore.user?.username ||
    previewAvatar.value !== null ||
    previewSignature.value !== null

  if (hasChanges) {
    if (confirm(t('editProfile.confirmUnsavedChanges'))) {
      router.push('/profile')
    }
  } else {
    router.push('/profile')
  }
}

function handlePhotoChange(event) {
  const file = event.target.files[0]
  if (file) {
    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      alert(t('editProfile.errors.photoTooLarge'))
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      previewAvatar.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

function handleSignatureChange(event) {
  const file = event.target.files[0]
  if (file) {
    if (file.size > 2 * 1024 * 1024) { // 2MB limit
      alert(t('editProfile.errors.signatureTooLarge'))
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      previewSignature.value = e.target.result
      form.value.signature = '' // Clear text signature
    }
    reader.readAsDataURL(file)
  }
}

function handleSwitchToProfessional() {
  // TODO: Implement professional account switch
  if (confirm(t('editProfile.confirmSwitchToProfessional'))) {
    // Navigate to artist registration or update user role
    router.push('/styles/create')
  }
}

function handleDeleteAccount() {
  if (confirm(t('editProfile.confirmDeleteAccount'))) {
    if (confirm(t('editProfile.confirmDeleteAccountFinal'))) {
      // TODO: Implement account deletion
      // await deleteUserAccount()
      // authStore.logout()
      // router.push('/')
      alert(t('editProfile.deleteNotImplemented'))
    }
  }
}
</script>

<style scoped>
/* Custom font for signature display */
.font-signature {
  font-family: 'Brush Script MT', cursive;
}
</style>
