/**
 * StyleCreate Page (Artist Only)
 *
 * Allows artists to create new style models by uploading training images,
 * providing metadata, and submitting for training.
 */
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useModelsStore } from '@/stores/models'
import { useAuthStore } from '@/stores/auth'
import { getMyStyle, updateModel } from '@/services/model.service'
import AppLayout from '@/components/layout/AppLayout.vue'
import Input from '@/components/shared/Input.vue'
import Button from '@/components/shared/Button.vue'
import Card from '@/components/shared/Card.vue'

const router = useRouter()
const { t } = useI18n()
const modelsStore = useModelsStore()
const authStore = useAuthStore()

// Loading state
const isCheckingExistingStyle = ref(true)

// Existing style (for edit mode)
const existingStyle = ref(null)

// Check if user already has an active style (MVP: 1 style per artist)
onMounted(async () => {
  isCheckingExistingStyle.value = true

  if (!authStore.user || authStore.user.role !== 'artist') {
    isCheckingExistingStyle.value = false
    return
  }

  try {
    // Get artist's existing style
    const response = await getMyStyle()

    if (response && response.data) {
      existingStyle.value = response.data

      // Load existing data into form for editing
      formData.value.name = existingStyle.value.name || ''
      formData.value.description = existingStyle.value.description || ''
      formData.value.price_per_generation = existingStyle.value.generation_cost_tokens || 10
    }
  } catch (err) {
    console.error('Failed to check existing style:', err)
  } finally {
    isCheckingExistingStyle.value = false
  }
})

// Computed: Edit mode if existing style exists
const isEditMode = computed(() => !!existingStyle.value)

// Form state
const formData = ref({
  name: '',
  description: '',
  price_per_generation: 10,
})

// Image upload state
const trainingImages = ref([])
const isDragging = ref(false)

// Submission state
const isSubmitting = ref(false)
const uploadProgress = ref(0)

// Validation errors
const errors = ref({})

// Computed
const isValid = computed(() => {
  // Edit mode: only name is required
  if (isEditMode.value) {
    return formData.value.name.trim() && Object.keys(errors.value).length === 0
  }

  // Create mode: name + training images required
  return (
    formData.value.name.trim() &&
    trainingImages.value.length >= 10 &&
    trainingImages.value.length <= 100 &&
    Object.keys(errors.value).length === 0
  )
})

const imageCountStatus = computed(() => {
  const count = trainingImages.value.length
  if (count < 10) return { text: t('styleCreate.imagesMinimum', { count }), color: 'text-red-600' }
  if (count > 100) return { text: t('styleCreate.imagesMaximum', { count }), color: 'text-red-600' }
  return { text: t('styleCreate.imagesSelected', { count }), color: 'text-green-600' }
})

// File validation
const validateImageFile = (file) => {
  const validTypes = ['image/jpeg', 'image/png', 'image/jpg']
  const maxSize = 10 * 1024 * 1024 // 10MB

  if (!validTypes.includes(file.type)) {
    return t('styleCreate.errors.invalidImageType')
  }

  if (file.size > maxSize) {
    return t('styleCreate.errors.imageTooLarge')
  }

  return null
}

// Handle file selection
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  addFiles(files)
}

// Handle drag and drop
const handleDrop = (event) => {
  event.preventDefault()
  isDragging.value = false

  const files = Array.from(event.dataTransfer.files)
  addFiles(files)
}

const handleDragOver = (event) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

// Add files with validation
const addFiles = (files) => {
  files.forEach((file) => {
    const error = validateImageFile(file)
    if (error) {
      console.error(`${file.name}: ${error}`)
      return
    }

    // Check for duplicates
    const isDuplicate = trainingImages.value.some(
      (img) => img.file.name === file.name && img.file.size === file.size
    )

    if (!isDuplicate && trainingImages.value.length < 100) {
      const reader = new FileReader()
      reader.onload = (e) => {
        trainingImages.value.push({
          file: file,
          preview: e.target.result,
          tags: [], // Tags for Stable Diffusion Fine-tuning
          tagInput: '', // Temp input for adding tags
          tagError: false, // Track validation error
        })
      }
      reader.readAsDataURL(file)
    }
  })
}

// Remove image
const removeImage = (index) => {
  trainingImages.value.splice(index, 1)
}

// Update tags for a training image
const updateImageTags = (index, tags) => {
  if (trainingImages.value[index]) {
    trainingImages.value[index].tags = tags
  }
}

// Filter to allow only English letters and spaces for tags
const filterTagEnglishOnly = (event, index) => {
  const input = event.target.value
  const filtered = input.replace(/[^a-zA-Z\s]/g, '')

  // Check if non-English characters were attempted
  if (input !== filtered) {
    trainingImages.value[index].tagError = true
    trainingImages.value[index].tagInput = filtered
    event.target.value = filtered
  } else {
    trainingImages.value[index].tagError = false
  }
}

// Add tag to a specific image
const addImageTag = (index, tag) => {
  if (!trainingImages.value[index]) return

  const trimmedTag = tag.trim()
  if (!trimmedTag) return

  // Validate English only
  const englishOnlyRegex = /^[a-zA-Z\s]*$/
  if (!englishOnlyRegex.test(trimmedTag)) {
    alert(t('styleCreate.errors.tagEnglishOnly'))
    return
  }

  if (!trainingImages.value[index].tags) {
    trainingImages.value[index].tags = []
  }

  if (!trainingImages.value[index].tags.includes(trimmedTag)) {
    trainingImages.value[index].tags.push(trimmedTag)
  }
}

// Remove tag from a specific image
const removeImageTag = (imageIndex, tagIndex) => {
  if (trainingImages.value[imageIndex]?.tags) {
    trainingImages.value[imageIndex].tags.splice(tagIndex, 1)
  }
}

// Validate form
const validateForm = () => {
  const newErrors = {}

  if (!formData.value.name.trim()) {
    newErrors.name = t('styleCreate.errors.styleNameRequired')
  }

  // Only validate images in create mode
  if (!isEditMode.value) {
    if (trainingImages.value.length < 10) {
      newErrors.images = t('styleCreate.errors.minimumImagesRequired')
    } else if (trainingImages.value.length > 100) {
      newErrors.images = t('styleCreate.errors.maximumImagesExceeded')
    }
  }

  if (formData.value.price_per_generation < 1) {
    newErrors.price = t('styleCreate.errors.minimumPrice')
  }

  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

// Submit form
const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  isSubmitting.value = true
  uploadProgress.value = 0

  try {
    if (isEditMode.value) {
      // Edit mode: Update existing style (name and description only)
      const data = {
        name: formData.value.name,
        description: formData.value.description,
      }

      await updateModel(existingStyle.value.id, data)

      // Show success message
      alert(t('styleCreate.updateSuccess'))

      // Redirect to marketplace after success
      router.push('/marketplace')
    } else {
      // Create mode: Create new style with training images
      const data = {
        name: formData.value.name,
        description: formData.value.description,
        generation_cost_tokens: formData.value.price_per_generation,
        training_images: trainingImages.value.map((img) => ({
          file: img.file,
          caption: img.tags?.join(', ') || '',
        })),
      }

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        uploadProgress.value = Math.min(uploadProgress.value + 10, 90)
      }, 500)

      // Create model
      await modelsStore.createModel(data)

      clearInterval(progressInterval)
      uploadProgress.value = 100

      // Redirect to marketplace after success
      setTimeout(() => {
        router.push('/marketplace')
      }, 500)
    }
  } catch (err) {
    console.error('Failed to save style:', err)
    const errorMessage = isEditMode.value
      ? t('styleCreate.errors.updateFailed')
      : t('styleCreate.errors.createFailed')
    errors.value.submit = err.response?.data?.error?.message || errorMessage
  } finally {
    isSubmitting.value = false
  }
}

// Reset form
const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
    price_per_generation: 10,
  }
  trainingImages.value = []
  errors.value = {}
}
</script>

<template>
  <AppLayout>
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Page Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-neutral-900 mb-2">
          {{ isEditMode ? $t('styleCreate.editTitle') : $t('styleCreate.title') }}
        </h1>
        <p class="text-neutral-600">
          {{ isEditMode ? $t('styleCreate.editSubtitle') : $t('styleCreate.subtitle') }}
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="isCheckingExistingStyle" class="flex justify-center items-center py-20">
        <div class="text-center">
          <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
          <p class="text-neutral-600">{{ $t('styleCreate.checkingExistingStyle') }}</p>
        </div>
      </div>

      <!-- Form -->
      <form v-if="!isCheckingExistingStyle" @submit.prevent="handleSubmit" class="space-y-8">
        <!-- Basic Info -->
        <Card>
          <h2 class="text-xl font-semibold text-neutral-900 mb-4">
            {{ $t('styleCreate.basicInfo') }}
          </h2>

          <div class="space-y-4">
            <!-- Style Name -->
            <Input
              v-model="formData.name"
              :label="$t('styleCreate.styleName')"
              :placeholder="$t('styleCreate.styleNamePlaceholder')"
              required
              :error="errors.name"
            />

            <!-- Description -->
            <Input
              v-model="formData.description"
              type="textarea"
              :label="$t('styleCreate.description')"
              :placeholder="$t('styleCreate.descriptionPlaceholder')"
              :helper="$t('styleCreate.descriptionHelper')"
            />

            <!-- Price -->
            <Input
              v-model.number="formData.price_per_generation"
              type="number"
              :label="$t('styleCreate.pricePerGeneration')"
              :min="1"
              required
              :error="errors.price"
            />
          </div>
        </Card>

        <!-- Training Images (Create Mode Only) -->
        <Card v-if="!isEditMode">
          <h2 class="text-xl font-semibold text-neutral-900 mb-2">
            {{ $t('styleCreate.trainingImages') }}
          </h2>
          <p class="text-sm text-neutral-600 mb-4">
            {{ $t('styleCreate.trainingImagesDescription') }}
          </p>

          <!-- Upload Count Status -->
          <div class="mb-4">
            <p :class="['font-medium', imageCountStatus.color]">
              {{ imageCountStatus.text }}
            </p>
          </div>

          <!-- Drag and Drop Zone -->
          <div
            class="border-2 border-dashed rounded-lg p-8 text-center transition-colors"
            :class="{
              'border-primary-500 bg-primary-50': isDragging,
              'border-neutral-300 bg-neutral-50': !isDragging,
            }"
            @drop="handleDrop"
            @dragover="handleDragOver"
            @dragleave="handleDragLeave"
          >
            <input
              ref="fileInput"
              type="file"
              multiple
              accept="image/jpeg,image/png,image/jpg"
              class="hidden"
              @change="handleFileSelect"
            />

            <svg
              class="w-12 h-12 mx-auto mb-4 text-neutral-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>

            <p class="text-lg font-medium text-neutral-900 mb-2">
              {{ $t('styleCreate.dropImagesHere') }}
            </p>
            <p class="text-sm text-neutral-600">
              {{ $t('styleCreate.fileFormats') }}
            </p>

            <Button
              type="button"
              variant="primary"
              class="mt-4"
              @click="$refs.fileInput.click()"
            >
              {{ $t('styleCreate.selectImages') }}
            </Button>
          </div>

          <!-- Error Message -->
          <p v-if="errors.images" class="mt-2 text-sm text-red-600">
            {{ errors.images }}
          </p>

          <!-- Image Horizontal Scroll Preview with Tags -->
          <div
            v-if="trainingImages.length > 0"
            class="mt-6 overflow-x-auto pb-4"
          >
            <div class="flex gap-4" style="min-width: max-content;">
              <div
                v-for="(image, index) in trainingImages"
                :key="index"
                class="w-80 flex-shrink-0 bg-white border border-neutral-200 rounded-lg p-3"
              >
                <!-- Image Preview -->
                <div class="relative aspect-square bg-neutral-100 rounded-lg overflow-hidden group mb-3">
                  <img
                    :src="image.preview"
                    :alt="`Training image ${index + 1}`"
                    class="w-full h-full object-cover"
                  />
                  <button
                    type="button"
                    class="absolute top-2 right-2 w-7 h-7 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center shadow-lg"
                    @click="removeImage(index)"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                  <div class="absolute bottom-2 left-2 px-2 py-1 bg-black bg-opacity-50 text-white text-xs rounded">
                    #{{ index + 1 }}
                  </div>
                </div>

                <!-- Tag Input -->
                <div>
                  <label class="block text-sm font-medium text-neutral-700 mb-2">
                    {{ $t('styleCreate.tagsForTraining') }}
                  </label>

                  <!-- Tag Input Field -->
                  <div>
                    <div class="flex gap-2 mb-2">
                      <input
                        v-model="image.tagInput"
                        type="text"
                        :placeholder="$t('styleCreate.addTagPlaceholder')"
                        :class="[
                          'flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 transition-colors',
                          image.tagError
                            ? 'border-red-500 focus:ring-red-500 bg-red-50'
                            : 'border-neutral-300 focus:ring-primary-500'
                        ]"
                        @input="filterTagEnglishOnly($event, index)"
                        @keydown.enter.prevent="addImageTag(index, image.tagInput); image.tagInput = ''"
                      />
                      <button
                        type="button"
                        class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
                        @click="addImageTag(index, image.tagInput); image.tagInput = ''"
                      >
                        {{ $t('styleCreate.addTagButton') }}
                      </button>
                    </div>
                    <p v-if="image.tagError" class="text-xs text-red-600 mb-2">
                      {{ $t('styleCreate.errors.tagEnglishOnly') }}
                    </p>
                  </div>

                  <!-- Tag Chips Display -->
                  <div v-if="image.tags?.length" class="flex flex-wrap gap-2 min-h-[32px]">
                    <button
                      v-for="(tag, tagIdx) in image.tags"
                      :key="tagIdx"
                      type="button"
                      class="group px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium hover:bg-primary-200 transition-colors flex items-center gap-1"
                      @click="removeImageTag(index, tagIdx)"
                    >
                      {{ tag }}
                      <svg class="w-3 h-3 opacity-60 group-hover:opacity-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  <p v-else class="text-xs text-neutral-400 italic min-h-[32px] flex items-center">
                    {{ $t('styleCreate.noTagsYet') }}
                  </p>

                  <p class="text-xs text-neutral-500 mt-2">
                    {{ $t('styleCreate.tagExamples') }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <!-- Submit Error -->
        <div v-if="errors.submit" class="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-red-800">{{ errors.submit }}</p>
        </div>

        <!-- Upload Progress -->
        <div v-if="isSubmitting" class="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p class="text-blue-800 mb-2">{{ $t('styleCreate.uploadingStyleModel') }}</p>
          <div class="w-full bg-blue-200 rounded-full h-2">
            <div
              class="bg-blue-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${uploadProgress}%` }"
            ></div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-4">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            :disabled="!isValid || isSubmitting"
            :loading="isSubmitting"
            fullWidth
          >
            {{ isEditMode ? $t('styleCreate.updateStyle') : $t('styleCreate.createStyle') }}
          </Button>
          <Button
            type="button"
            variant="outline"
            size="lg"
            @click="router.push('/marketplace')"
            :disabled="isSubmitting"
          >
            {{ $t('styleCreate.cancel') }}
          </Button>
        </div>
      </form>
    </div>
  </AppLayout>
</template>
