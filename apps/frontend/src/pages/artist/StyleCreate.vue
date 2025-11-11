/**
 * StyleCreate Page (Artist Only)
 *
 * Allows artists to create new style models by uploading training images,
 * providing metadata, and submitting for training.
 */
<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useModelsStore } from '@/stores/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import Input from '@/components/shared/Input.vue'
import Button from '@/components/shared/Button.vue'
import Card from '@/components/shared/Card.vue'

const router = useRouter()
const modelsStore = useModelsStore()

// Form state
const formData = ref({
  name: '',
  description: '',
  price_per_generation: 10,
  tags: [],
})

// Image upload state
const trainingImages = ref([])
const signatureImage = ref(null)
const isDragging = ref(false)

// Tag input
const tagInput = ref('')

// Submission state
const isSubmitting = ref(false)
const uploadProgress = ref(0)

// Validation errors
const errors = ref({})

// Computed
const isValid = computed(() => {
  return (
    formData.value.name.trim() &&
    trainingImages.value.length >= 10 &&
    trainingImages.value.length <= 100 &&
    Object.keys(errors.value).length === 0
  )
})

const imageCountStatus = computed(() => {
  const count = trainingImages.value.length
  if (count < 10) return { text: `${count}/10 minimum`, color: 'text-red-600' }
  if (count > 100) return { text: `${count}/100 maximum (too many!)`, color: 'text-red-600' }
  return { text: `${count} images selected`, color: 'text-green-600' }
})

// File validation
const validateImageFile = (file) => {
  const validTypes = ['image/jpeg', 'image/png', 'image/jpg']
  const maxSize = 10 * 1024 * 1024 // 10MB

  if (!validTypes.includes(file.type)) {
    return 'Only JPG and PNG images are allowed'
  }

  if (file.size > maxSize) {
    return 'Image size must be less than 10MB'
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

// Handle signature upload
const handleSignatureUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return

  const error = validateImageFile(file)
  if (error) {
    alert(error)
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    signatureImage.value = {
      file: file,
      preview: e.target.result,
    }
  }
  reader.readAsDataURL(file)
}

// Remove signature
const removeSignature = () => {
  signatureImage.value = null
}

// Add tag
const addTag = () => {
  const tag = tagInput.value.trim()
  if (tag && !formData.value.tags.includes(tag)) {
    formData.value.tags.push(tag)
    tagInput.value = ''
  }
}

// Remove tag
const removeTag = (index) => {
  formData.value.tags.splice(index, 1)
}

// Validate form
const validateForm = () => {
  const newErrors = {}

  if (!formData.value.name.trim()) {
    newErrors.name = 'Style name is required'
  }

  if (trainingImages.value.length < 10) {
    newErrors.images = 'At least 10 training images are required'
  } else if (trainingImages.value.length > 100) {
    newErrors.images = 'Maximum 100 training images allowed'
  }

  if (formData.value.price_per_generation < 1) {
    newErrors.price = 'Price must be at least 1 token'
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
    // Prepare data
    const data = {
      name: formData.value.name,
      description: formData.value.description,
      price_per_generation: formData.value.price_per_generation,
      tags: formData.value.tags,
      training_images: trainingImages.value.map((img) => img.file),
    }

    // Add signature if provided
    if (signatureImage.value) {
      data.signature_image = signatureImage.value.file
    }

    // Simulate upload progress (real progress tracking would need backend support)
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
  } catch (err) {
    console.error('Failed to create style:', err)
    errors.value.submit = err.response?.data?.error?.message || 'Failed to create style'
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
    tags: [],
  }
  trainingImages.value = []
  signatureImage.value = null
  tagInput.value = ''
  errors.value = {}
}
</script>

<template>
  <AppLayout>
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Page Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-neutral-900 mb-2">
          Create New Style
        </h1>
        <p class="text-neutral-600">
          Upload your artwork to train a custom AI style model
        </p>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-8">
        <!-- Basic Info -->
        <Card>
          <h2 class="text-xl font-semibold text-neutral-900 mb-4">
            Basic Information
          </h2>

          <div class="space-y-4">
            <!-- Style Name -->
            <Input
              v-model="formData.name"
              label="Style Name"
              placeholder="e.g., Watercolor Dreams"
              required
              :error="errors.name"
            />

            <!-- Description -->
            <Input
              v-model="formData.description"
              type="textarea"
              label="Description"
              placeholder="Describe your art style..."
              helper="Optional: Tell users about this style"
            />

            <!-- Price -->
            <Input
              v-model.number="formData.price_per_generation"
              type="number"
              label="Price per Generation (tokens)"
              :min="1"
              required
              :error="errors.price"
            />
          </div>
        </Card>

        <!-- Training Images -->
        <Card>
          <h2 class="text-xl font-semibold text-neutral-900 mb-2">
            Training Images
          </h2>
          <p class="text-sm text-neutral-600 mb-4">
            Upload 10-100 images that represent your style. Higher quality and more diverse images lead to better results.
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
              Drop images here or click to browse
            </p>
            <p class="text-sm text-neutral-600">
              JPG or PNG, max 10MB each
            </p>

            <Button
              type="button"
              variant="primary"
              class="mt-4"
              @click="$refs.fileInput.click()"
            >
              Select Images
            </Button>
          </div>

          <!-- Error Message -->
          <p v-if="errors.images" class="mt-2 text-sm text-red-600">
            {{ errors.images }}
          </p>

          <!-- Image Grid Preview -->
          <div
            v-if="trainingImages.length > 0"
            class="mt-6 grid grid-cols-4 sm:grid-cols-6 gap-3"
          >
            <div
              v-for="(image, index) in trainingImages"
              :key="index"
              class="relative aspect-square bg-neutral-100 rounded-lg overflow-hidden group"
            >
              <img
                :src="image.preview"
                :alt="`Training image ${index + 1}`"
                class="w-full h-full object-cover"
              />
              <button
                type="button"
                class="absolute top-1 right-1 w-6 h-6 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                @click="removeImage(index)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </Card>

        <!-- Tags -->
        <Card>
          <h2 class="text-xl font-semibold text-neutral-900 mb-4">
            Tags
          </h2>

          <div class="flex gap-2 mb-3">
            <Input
              v-model="tagInput"
              placeholder="Add tags (e.g., watercolor, portrait, vibrant)"
              @keydown.enter.prevent="addTag"
            />
            <Button type="button" variant="outline" @click="addTag">
              Add
            </Button>
          </div>

          <div v-if="formData.tags.length > 0" class="flex flex-wrap gap-2">
            <button
              v-for="(tag, index) in formData.tags"
              :key="index"
              type="button"
              class="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm flex items-center gap-1 hover:bg-primary-200 transition-colors"
              @click="removeTag(index)"
            >
              {{ tag }}
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </Card>

        <!-- Signature (Optional) -->
        <Card>
          <h2 class="text-xl font-semibold text-neutral-900 mb-2">
            Signature (Optional)
          </h2>
          <p class="text-sm text-neutral-600 mb-4">
            Upload your signature to be embedded in generated images as a watermark
          </p>

          <div v-if="!signatureImage" class="border-2 border-dashed border-neutral-300 rounded-lg p-6 text-center bg-neutral-50">
            <input
              ref="signatureInput"
              type="file"
              accept="image/png"
              class="hidden"
              @change="handleSignatureUpload"
            />

            <Button
              type="button"
              variant="outline"
              @click="$refs.signatureInput.click()"
            >
              Upload Signature
            </Button>
            <p class="text-xs text-neutral-500 mt-2">
              PNG format recommended for transparency
            </p>
          </div>

          <div v-else class="flex items-center gap-4">
            <img
              :src="signatureImage.preview"
              alt="Signature preview"
              class="h-16 border border-neutral-200 rounded"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              @click="removeSignature"
            >
              Remove
            </Button>
          </div>
        </Card>

        <!-- Submit Error -->
        <div v-if="errors.submit" class="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-red-800">{{ errors.submit }}</p>
        </div>

        <!-- Upload Progress -->
        <div v-if="isSubmitting" class="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p class="text-blue-800 mb-2">Uploading style model...</p>
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
            Create Style
          </Button>
          <Button
            type="button"
            variant="outline"
            size="lg"
            @click="router.push('/marketplace')"
            :disabled="isSubmitting"
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  </AppLayout>
</template>
