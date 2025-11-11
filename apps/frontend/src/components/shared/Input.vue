<template>
  <div class="w-full">
    <!-- Label -->
    <label v-if="label" :for="inputId" class="block text-sm font-medium text-neutral-700 mb-1">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>

    <!-- Input or Textarea -->
    <textarea
      v-if="type === 'textarea'"
      :id="inputId"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :rows="rows"
      :class="inputClasses"
      @input="handleInput"
      @blur="$emit('blur', $event)"
      @focus="$emit('focus', $event)"
    />
    <input
      v-else
      :id="inputId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :min="min"
      :max="max"
      :step="step"
      :class="inputClasses"
      @input="handleInput"
      @blur="$emit('blur', $event)"
      @focus="$emit('focus', $event)"
    />

    <!-- Helper text or error -->
    <p v-if="error" class="mt-1 text-sm text-red-600">
      {{ error }}
    </p>
    <p v-else-if="helperText" class="mt-1 text-sm text-neutral-500">
      {{ helperText }}
    </p>

    <!-- Slot for custom helper content -->
    <div v-if="$slots.helper" class="mt-1">
      <slot name="helper" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  type: {
    type: String,
    default: 'text',
    validator: (value) => ['text', 'email', 'number', 'password', 'textarea'].includes(value),
  },
  label: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  helperText: {
    type: String,
    default: '',
  },
  error: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  required: {
    type: Boolean,
    default: false,
  },
  rows: {
    type: Number,
    default: 4,
  },
  min: {
    type: Number,
    default: undefined,
  },
  max: {
    type: Number,
    default: undefined,
  },
  step: {
    type: Number,
    default: undefined,
  },
})

const emit = defineEmits(['update:modelValue', 'blur', 'focus'])

const inputId = computed(() => {
  return `input-${Math.random().toString(36).substring(7)}`
})

const handleInput = (event) => {
  const value = event.target.value
  emit('update:modelValue', props.type === 'number' ? Number(value) : value)
}

const inputClasses = computed(() => {
  const classes = [
    'block',
    'w-full',
    'rounded-lg',
    'border',
    'px-4',
    'py-2',
    'text-neutral-900',
    'placeholder-neutral-400',
    'transition-colors',
    'duration-200',
    'focus:outline-none',
    'focus:ring-2',
    'focus:ring-offset-0',
  ]

  if (props.error) {
    classes.push(
      'border-red-500',
      'focus:border-red-500',
      'focus:ring-red-500'
    )
  } else {
    classes.push(
      'border-neutral-300',
      'focus:border-primary-500',
      'focus:ring-primary-500'
    )
  }

  if (props.disabled) {
    classes.push(
      'bg-neutral-100',
      'cursor-not-allowed',
      'text-neutral-500'
    )
  } else {
    classes.push('bg-white')
  }

  if (props.type === 'textarea') {
    classes.push('resize-y')
  }

  return classes.join(' ')
})
</script>
