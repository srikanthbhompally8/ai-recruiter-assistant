import { configureStore } from '@reduxjs/toolkit'

// Import slices (to be created)
// import authSlice from './slices/authSlice'
// import candidateSlice from './slices/candidateSlice'
// import jobSlice from './slices/jobSlice'

export const store = configureStore({
  reducer: {
    // auth: authSlice,
    // candidates: candidateSlice,
    // jobs: jobSlice,
  },
})

export default store
