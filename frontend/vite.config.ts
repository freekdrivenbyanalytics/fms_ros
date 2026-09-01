import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(import.meta.dirname,'index.html'),
        customerPortal: resolve(import.meta.dirname,'customer-portal.html'),
        employeeManagement: resolve(import.meta.dirname,'employee-management.html'),
        adminPortal: resolve(import.meta.dirname,'admin-portal.html'),
      },
    },
  },
})
