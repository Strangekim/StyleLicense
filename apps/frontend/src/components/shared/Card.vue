<template>
  <component
    :is="clickable ? 'button' : 'div'"
    :type="clickable ? 'button' : undefined"
    :class="cardClasses"
    @click="handleClick"
  >
    <slot />
  </component>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  clickable: {
    type: Boolean,
    default: false,
  },
  variant: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'bordered', 'elevated'].includes(value),
  },
  padding: {
    type: String,
    default: 'md',
    validator: (value) => ['none', 'sm', 'md', 'lg'].includes(value),
  },
})

const emit = defineEmits(['click'])

const handleClick = (event) => {
  if (props.clickable) {
    emit('click', event)
  }
}

const cardClasses = computed(() => {
  const classes = [
    'rounded-lg',
    'transition-all',
    'duration-200',
  ]

  // Variant styles
  const variantClasses = {
    default: ['bg-white', 'border', 'border-neutral-200'],
    bordered: ['bg-white', 'border-2', 'border-neutral-300'],
    elevated: ['bg-white', 'shadow-card'],
  }
  classes.push(...variantClasses[props.variant])

  // Padding
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }
  if (paddingClasses[props.padding]) {
    classes.push(paddingClasses[props.padding])
  }

  // Clickable styles
  if (props.clickable) {
    classes.push(
      'cursor-pointer',
      'hover:shadow-soft',
      'hover:scale-[1.02]',
      'active:scale-[0.98]',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-primary-500',
      'focus:ring-offset-2',
      'text-left',
      'w-full'
    )
  }

  return classes.join(' ')
})
</script>
