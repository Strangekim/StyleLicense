/**
 * SignatureCanvas Component
 *
 * Allows users to draw their signature on a canvas
 */
<template>
  <div class="signature-canvas-container">
    <div class="border-2 border-gray-300 rounded-lg bg-white relative">
      <canvas
        ref="canvasRef"
        :width="width"
        :height="height"
        class="cursor-crosshair touch-none"
        @mousedown="startDrawing"
        @mousemove="draw"
        @mouseup="stopDrawing"
        @mouseleave="stopDrawing"
        @touchstart.prevent="handleTouchStart"
        @touchmove.prevent="handleTouchMove"
        @touchend.prevent="stopDrawing"
      ></canvas>

      <!-- Clear Button -->
      <button
        v-if="!isEmpty"
        type="button"
        @click="clear"
        class="absolute top-2 right-2 px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-colors"
      >
        {{ $t('signatureCanvas.clear') || 'Clear' }}
      </button>
    </div>

    <!-- Helper Text -->
    <p class="text-xs text-gray-500 mt-2">
      {{ $t('signatureCanvas.drawYourSignature') || 'Draw your signature above' }}
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted, defineExpose } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  width: {
    type: Number,
    default: 400
  },
  height: {
    type: Number,
    default: 150
  },
  lineWidth: {
    type: Number,
    default: 2
  },
  strokeColor: {
    type: String,
    default: '#000000'
  }
})

const emit = defineEmits(['update:signature'])

const canvasRef = ref(null)
const context = ref(null)
const isDrawing = ref(false)
const isEmpty = ref(true)
const lastX = ref(0)
const lastY = ref(0)

onMounted(() => {
  if (canvasRef.value) {
    context.value = canvasRef.value.getContext('2d')
    context.value.strokeStyle = props.strokeColor
    context.value.lineWidth = props.lineWidth
    context.value.lineCap = 'round'
    context.value.lineJoin = 'round'
  }
})

function startDrawing(event) {
  isDrawing.value = true
  const rect = canvasRef.value.getBoundingClientRect()
  lastX.value = event.clientX - rect.left
  lastY.value = event.clientY - rect.top

  // Start new path
  context.value.beginPath()
  context.value.moveTo(lastX.value, lastY.value)
}

function draw(event) {
  if (!isDrawing.value) return

  const rect = canvasRef.value.getBoundingClientRect()
  const currentX = event.clientX - rect.left
  const currentY = event.clientY - rect.top

  context.value.lineTo(currentX, currentY)
  context.value.stroke()

  lastX.value = currentX
  lastY.value = currentY
  isEmpty.value = false
}

function stopDrawing() {
  if (isDrawing.value) {
    isDrawing.value = false
    emitSignature()
  }
}

function handleTouchStart(event) {
  const touch = event.touches[0]
  const rect = canvasRef.value.getBoundingClientRect()

  isDrawing.value = true
  lastX.value = touch.clientX - rect.left
  lastY.value = touch.clientY - rect.top

  context.value.beginPath()
  context.value.moveTo(lastX.value, lastY.value)
}

function handleTouchMove(event) {
  if (!isDrawing.value) return

  const touch = event.touches[0]
  const rect = canvasRef.value.getBoundingClientRect()
  const currentX = touch.clientX - rect.left
  const currentY = touch.clientY - rect.top

  context.value.lineTo(currentX, currentY)
  context.value.stroke()

  lastX.value = currentX
  lastY.value = currentY
  isEmpty.value = false
}

function clear() {
  context.value.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  isEmpty.value = true
  emit('update:signature', null)
}

function emitSignature() {
  if (!isEmpty.value) {
    emit('update:signature', getSignatureData())
  }
}

function getSignatureData() {
  // Return canvas as data URL (PNG)
  return canvasRef.value.toDataURL('image/png')
}

function getSignatureBlob() {
  return new Promise((resolve) => {
    canvasRef.value.toBlob((blob) => {
      resolve(blob)
    }, 'image/png')
  })
}

function setSignature(dataUrl) {
  const img = new Image()
  img.onload = () => {
    context.value.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
    context.value.drawImage(img, 0, 0)
    isEmpty.value = false
  }
  img.src = dataUrl
}

// Expose methods for parent components
defineExpose({
  clear,
  getSignatureData,
  getSignatureBlob,
  setSignature,
  isEmpty: () => isEmpty.value
})
</script>

<style scoped>
.signature-canvas-container {
  width: 100%;
}

canvas {
  display: block;
  width: 100%;
  height: auto;
}
</style>
