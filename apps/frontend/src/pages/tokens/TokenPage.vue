<template>
  <div class="min-h-screen bg-gray-50">
    <AppLayout>
      <div class="max-w-4xl mx-auto px-4 py-6">
        <!-- Page Header -->
        <div class="mb-6">
          <h1 class="text-3xl font-bold text-gray-900">{{ $t('tokens.balance') }}</h1>
          <p class="mt-2 text-gray-600">{{ $t('tokens.manageTokens') }}</p>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>

        <!-- Token Balance Card -->
        <div v-else class="bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg shadow-lg p-8 mb-6 text-white">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-blue-100 text-sm font-medium mb-2">{{ $t('tokens.currentBalance') }}</p>
              <p class="text-5xl font-bold">{{ tokenBalance.toLocaleString() }}</p>
              <p class="text-blue-100 text-sm mt-2">{{ $t('tokens.tokenUnit') }}</p>
            </div>
            <div class="text-right">
              <svg class="w-20 h-20 text-blue-300 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Purchase Tokens Section -->
        <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">{{ $t('tokens.purchase') }}</h2>
          <p class="text-sm text-gray-600 mb-6">{{ $t('tokens.selectPackage') }}</p>

          <!-- Token Packages Grid -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div
              v-for="pkg in tokenPackages"
              :key="pkg.id"
              class="border-2 rounded-lg p-6 hover:border-blue-500 transition-colors cursor-pointer"
              :class="{
                'border-blue-500 bg-blue-50': selectedPackage?.id === pkg.id,
                'border-gray-200': selectedPackage?.id !== pkg.id,
              }"
              @click="selectedPackage = pkg"
            >
              <!-- Popular Badge -->
              <div v-if="pkg.popular" class="mb-2">
                <span class="inline-block px-2 py-1 bg-blue-600 text-white text-xs font-semibold rounded-full">
                  {{ $t('tokens.popular') }}
                </span>
              </div>

              <!-- Package Info -->
              <div class="text-center">
                <p class="text-3xl font-bold text-gray-900">{{ pkg.tokens.toLocaleString() }}</p>
                <p class="text-sm text-gray-600 mt-1">{{ $t('tokens.tokenUnit') }}</p>
                <div class="mt-4 mb-4 border-t border-gray-200"></div>
                <p class="text-2xl font-bold text-blue-600">${{ pkg.price }}</p>
                <p class="text-xs text-gray-500 mt-1">${{ (pkg.price / pkg.tokens).toFixed(3) }} {{ $t('tokens.perToken') }}</p>

                <!-- Bonus Badge -->
                <div v-if="pkg.bonus" class="mt-3">
                  <span class="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                    +{{ pkg.bonus }}% {{ $t('tokens.bonus') }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Purchase Button -->
          <div class="mt-6 text-center">
            <button
              @click="handlePurchase"
              :disabled="!selectedPackage || purchasing"
              class="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {{ purchasing ? $t('tokens.processing') : $t('tokens.purchaseButton') }}
            </button>
            <p class="mt-2 text-xs text-gray-500">
              {{ $t('tokens.securePayment') }}
            </p>
          </div>
        </div>

        <!-- Transaction History -->
        <div class="bg-white rounded-lg shadow-sm p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">{{ $t('tokens.transactionHistory') }}</h2>

          <!-- Loading Transactions -->
          <div v-if="loadingTransactions" class="text-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>

          <!-- Empty State -->
          <div v-else-if="transactions.length === 0" class="text-center py-8">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p class="mt-2 text-sm text-gray-600">{{ $t('tokens.noTransactions') }}</p>
          </div>

          <!-- Transaction List -->
          <div v-else class="space-y-3">
            <div
              v-for="transaction in transactions"
              :key="transaction.id"
              class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <!-- Transaction Info -->
              <div class="flex items-center space-x-4">
                <!-- Icon -->
                <div
                  class="w-10 h-10 rounded-full flex items-center justify-center"
                  :class="getTransactionIconClass(transaction.type)"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path v-if="transaction.type === 'purchase'" d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                    <path v-if="transaction.type === 'purchase'" fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clip-rule="evenodd" />
                    <path v-else-if="transaction.type === 'usage'" d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                    <path v-else-if="transaction.type === 'usage'" fill-rule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd" />
                  </svg>
                </div>

                <!-- Details -->
                <div>
                  <p class="font-semibold text-gray-900">{{ transaction.description }}</p>
                  <p class="text-xs text-gray-500">{{ formatTime(transaction.created_at) }}</p>
                </div>
              </div>

              <!-- Amount -->
              <div class="text-right">
                <p
                  class="font-semibold"
                  :class="{
                    'text-green-600': transaction.type === 'purchase',
                    'text-red-600': transaction.type === 'usage',
                  }"
                >
                  {{ transaction.type === 'purchase' ? '+' : '-' }}{{ Math.abs(transaction.amount).toLocaleString() }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ transaction.type === 'purchase' ? $t('tokens.purchased') : $t('tokens.used') }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppLayout from '@/components/layout/AppLayout.vue'

const router = useRouter()
const { t, locale } = useI18n()

// State
const loading = ref(false)
const loadingTransactions = ref(false)
const purchasing = ref(false)
const tokenBalance = ref(0)
const selectedPackage = ref(null)
const transactions = ref([])

// Token packages
const tokenPackages = [
  {
    id: 1,
    tokens: 100,
    price: 9.99,
    bonus: 0,
    popular: false,
  },
  {
    id: 2,
    tokens: 500,
    price: 44.99,
    bonus: 10,
    popular: true,
  },
  {
    id: 3,
    tokens: 1000,
    price: 79.99,
    bonus: 20,
    popular: false,
  },
]

// Methods
onMounted(async () => {
  await loadTokenBalance()
  await loadTransactions()
})

async function loadTokenBalance() {
  loading.value = true
  try {
    // TODO: Replace with actual API call
    // const response = await getTokenBalance()
    // tokenBalance.value = response.data.balance

    // Mock data
    tokenBalance.value = 250
  } catch (error) {
    console.error('Failed to load token balance:', error)
  } finally {
    loading.value = false
  }
}

async function loadTransactions() {
  loadingTransactions.value = true
  try {
    // TODO: Replace with actual API call
    // const response = await getTokenTransactions()
    // transactions.value = response.data

    // Mock data
    transactions.value = [
      {
        id: 1,
        type: 'purchase',
        amount: 500,
        description: 'Purchased 500 tokens',
        created_at: new Date(Date.now() - 86400000).toISOString(),
      },
      {
        id: 2,
        type: 'usage',
        amount: -50,
        description: 'Generated image with Van Gogh style',
        created_at: new Date(Date.now() - 172800000).toISOString(),
      },
      {
        id: 3,
        type: 'usage',
        amount: -100,
        description: 'Purchased Van Gogh style',
        created_at: new Date(Date.now() - 259200000).toISOString(),
      },
      {
        id: 4,
        type: 'usage',
        amount: -50,
        description: 'Generated image with Anime style',
        created_at: new Date(Date.now() - 345600000).toISOString(),
      },
      {
        id: 5,
        type: 'usage',
        amount: -50,
        description: 'Generated image with Portrait style',
        created_at: new Date(Date.now() - 432000000).toISOString(),
      },
    ]
  } catch (error) {
    console.error('Failed to load transactions:', error)
  } finally {
    loadingTransactions.value = false
  }
}

async function handlePurchase() {
  if (!selectedPackage.value || purchasing.value) return

  purchasing.value = true
  try {
    // TODO: Replace with actual payment flow
    // const response = await createPaymentSession({
    //   package_id: selectedPackage.value.id,
    //   amount: selectedPackage.value.price,
    // })
    // window.location.href = response.data.checkout_url

    // Mock: Simulate purchase
    alert(t('tokens.purchasingMessage', { tokens: selectedPackage.value.tokens, price: selectedPackage.value.price }))

    // In production, this would redirect to Stripe checkout
    // For now, just simulate success
    await new Promise(resolve => setTimeout(resolve, 1000))

    // Update balance
    tokenBalance.value += selectedPackage.value.tokens

    // Add transaction
    transactions.value.unshift({
      id: Date.now(),
      type: 'purchase',
      amount: selectedPackage.value.tokens,
      description: t('tokens.purchasedTokens', { tokens: selectedPackage.value.tokens }),
      created_at: new Date().toISOString(),
    })

    // Clear selection
    selectedPackage.value = null

    alert(t('tokens.purchaseSuccess'))
  } catch (error) {
    console.error('Failed to purchase tokens:', error)
    alert(t('tokens.purchaseFailed'))
  } finally {
    purchasing.value = false
  }
}

function getTransactionIconClass(type) {
  return type === 'purchase'
    ? 'bg-green-100 text-green-600'
    : 'bg-red-100 text-red-600'
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)

  if (diffInSeconds < 60) {
    return t('common.justNow')
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return t('common.minutesAgo', { n: minutes })
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return t('common.hoursAgo', { n: hours })
  } else if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400)
    return t('common.daysAgo', { n: days })
  } else {
    const localeStr = locale.value === 'ko' ? 'ko-KR' : 'en-US'
    return date.toLocaleDateString(localeStr, {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    })
  }
}
</script>
