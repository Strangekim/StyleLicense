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
            placeholder="email@example.com"
            disabled
          />
          <p class="mt-1 text-xs text-gray-500">
            {{ $t('editProfile.emailCannotBeChanged') }}
          </p>
        </div>

        <!-- Signature (Required for Artist) -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            {{ $t('editProfile.signature') }}
            <span v-if="!isProfessional" class="text-red-600">*</span>
          </label>
          <p class="text-xs text-gray-500 mb-3">
            {{ $t('editProfile.signatureRequiredForArtist') || 'Signature is required to upgrade to artist account' }}
          </p>

          <!-- Mode Tabs -->
          <div class="flex gap-2 mb-3">
            <button
              type="button"
              @click="signatureMode = 'canvas'"
              :class="[
                'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                signatureMode === 'canvas'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              {{ $t('editProfile.drawSignature') || 'Draw' }}
            </button>
            <button
              type="button"
              @click="signatureMode = 'image'"
              :class="[
                'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                signatureMode === 'image'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              {{ $t('editProfile.uploadSignature') || 'Upload' }}
            </button>
          </div>

          <!-- Canvas Drawing Mode -->
          <div v-if="signatureMode === 'canvas'">
            <SignatureCanvas
              ref="signatureCanvasRef"
              :width="400"
              :height="150"
              @update:signature="handleSignatureCanvasUpdate"
            />
          </div>

          <!-- Image Upload Mode -->
          <div v-else-if="signatureMode === 'image'">
            <div v-if="!previewSignatureImage" class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center bg-gray-50">
              <label class="cursor-pointer">
                <svg class="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p class="text-sm text-gray-600 mb-2">{{ $t('editProfile.uploadSignatureImage') || 'Upload signature image' }}</p>
                <p class="text-xs text-gray-500">PNG, JPG (max 2MB)</p>
                <input
                  type="file"
                  accept="image/*"
                  @change="handleSignatureImageUpload"
                  class="hidden"
                />
              </label>
            </div>
            <div v-else class="border border-gray-300 rounded-lg p-4 bg-gray-50">
              <img
                :src="previewSignatureImage"
                alt="Signature"
                class="max-h-32 mx-auto object-contain mb-2"
              />
              <button
                type="button"
                @click="clearSignature"
                class="w-full px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm"
              >
                {{ $t('editProfile.clearSignature') || 'Clear' }}
              </button>
            </div>
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { updateUserProfile, upgradeToArtist } from '@/services/user.service'
import SignatureCanvas from '@/components/signature/SignatureCanvas.vue'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

// State
const loading = ref(false)
const saving = ref(false)
const isProfessional = ref(false)
const previewAvatar = ref(null)
const avatarFile = ref(null)

// Signature state
const signatureCanvasRef = ref(null)
const signatureDrawingData = ref(null) // Canvas drawing as data URL
const signatureImageFile = ref(null) // Uploaded signature image file
const previewSignatureImage = ref(null) // Preview for uploaded image
const signatureMode = ref('canvas') // 'canvas' or 'image'

const form = ref({
  username: '',
  bio: '',
  email: '',
  avatar: null,
})

// Computed: Check if user has provided any signature
const hasSignature = computed(() => {
  return signatureDrawingData.value || signatureImageFile.value || previewSignatureImage.value
})

// Methods
onMounted(async () => {
  await loadProfile()
})

async function loadProfile() {
  loading.value = true
  try {
    console.log('[DEBUG] Loading profile...')
    console.log('[DEBUG] Auth user:', authStore.user)

    // Load profile data from auth store
    if (authStore.user) {
      form.value = {
        username: authStore.user.username || '',
        bio: authStore.user.bio || '',
        email: authStore.user.email || '',
        avatar: authStore.user.profile_image || null,
      }

      console.log('[DEBUG] User role:', authStore.user.role)
      console.log('[DEBUG] Artist object:', authStore.user.artist)
      console.log('[DEBUG] Signature URL from artist:', authStore.user.artist?.signature_image_url)

      // Load existing signature if artist
      if (authStore.user.artist?.signature_image_url) {
        console.log('[DEBUG] Loading existing signature:', authStore.user.artist.signature_image_url)
        previewSignatureImage.value = authStore.user.artist.signature_image_url
        signatureMode.value = 'image'
      } else {
        console.log('[DEBUG] No existing signature found')
      }

      // Check if user is professional (artist)
      isProfessional.value = authStore.user.role === 'artist'
      console.log('[DEBUG] Is professional:', isProfessional.value)
    }
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
    const updateData = {
      username: form.value.username,
      bio: form.value.bio,
    }

    // Add profile image if changed
    if (avatarFile.value) {
      updateData.profile_image = avatarFile.value
    }

    // Add signature if provided
    console.log('[DEBUG] Signature mode:', signatureMode.value)
    console.log('[DEBUG] Canvas data:', signatureDrawingData.value ? 'exists' : 'null')
    console.log('[DEBUG] Image file:', signatureImageFile.value ? 'exists' : 'null')
    console.log('[DEBUG] Preview image:', previewSignatureImage.value ? 'exists' : 'null')

    if (signatureMode.value === 'canvas' && signatureDrawingData.value) {
      console.log('[DEBUG] Adding canvas signature to update')
      // Convert canvas data URL to blob
      const blob = await fetch(signatureDrawingData.value).then(r => r.blob())
      const file = new File([blob], 'signature_canvas.png', { type: 'image/png' })
      updateData.signature_image = file
    } else if (signatureMode.value === 'image' && signatureImageFile.value) {
      console.log('[DEBUG] Adding image signature to update')
      updateData.signature_image = signatureImageFile.value
    } else {
      console.log('[DEBUG] No new signature to upload')
    }

    console.log('[DEBUG] Update data keys:', Object.keys(updateData))

    // Call backend API to update profile
    const response = await updateUserProfile(updateData)
    console.log('[DEBUG] Backend response:', response)

    if (response.success) {
      console.log('[DEBUG] Profile update successful, refreshing auth...')
      // Update auth store with new data
      await authStore.initAuth() // Refresh user data from backend

      console.log('[DEBUG] Auth refreshed. User data:', authStore.user)
      console.log('[DEBUG] Artist data:', authStore.user?.artist)
      console.log('[DEBUG] Signature URL:', authStore.user?.artist?.signature_image_url)

      // Navigate back to profile
      router.push('/profile')
    } else {
      throw new Error(response.error?.message || 'Update failed')
    }
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

    // Store the file for upload
    avatarFile.value = file

    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => {
      previewAvatar.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

function handleSignatureCanvasUpdate(dataUrl) {
  signatureDrawingData.value = dataUrl
  signatureMode.value = 'canvas'
}

function handleSignatureImageUpload(event) {
  const file = event.target.files[0]
  if (file) {
    if (file.size > 2 * 1024 * 1024) { // 2MB limit
      alert(t('editProfile.errors.signatureTooLarge'))
      return
    }

    // Store the file for upload
    signatureImageFile.value = file
    signatureMode.value = 'image'

    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => {
      previewSignatureImage.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

function clearSignature() {
  signatureDrawingData.value = null
  signatureImageFile.value = null
  previewSignatureImage.value = null
  signatureMode.value = 'canvas'
  if (signatureCanvasRef.value) {
    signatureCanvasRef.value.clear()
  }
}

async function handleSwitchToProfessional() {
  // IMPORTANT: Validate signature before allowing upgrade
  if (!hasSignature.value) {
    alert(t('editProfile.errors.signatureRequired') || 'Please provide your signature before upgrading to artist account.')
    return
  }

  if (!confirm(t('editProfile.confirmSwitchToProfessional'))) {
    return
  }

  try {
    // First, save the signature
    saving.value = true
    const updateData = {}

    // Add signature to update data
    if (signatureMode.value === 'canvas' && signatureDrawingData.value) {
      const blob = await fetch(signatureDrawingData.value).then(r => r.blob())
      const file = new File([blob], 'signature_canvas.png', { type: 'image/png' })
      updateData.signature_image = file
    } else if (signatureMode.value === 'image' && signatureImageFile.value) {
      updateData.signature_image = signatureImageFile.value
    }

    // Save signature first
    await updateUserProfile(updateData)

    // Then upgrade to artist
    const response = await upgradeToArtist()

    if (response.success) {
      // Update auth store with new user data
      await authStore.initAuth()

      // Show success message
      alert(t('editProfile.upgradedToArtist') || 'Successfully upgraded to artist account!')

      // Navigate to style creation page
      router.push('/styles/create')
    } else {
      throw new Error(response.error?.message || 'Upgrade failed')
    }
  } catch (error) {
    console.error('Failed to upgrade to artist:', error)
    alert(t('editProfile.errors.upgradeFailed') || 'Failed to upgrade to artist account. Please try again.')
  } finally {
    saving.value = false
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
